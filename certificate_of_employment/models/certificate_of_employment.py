from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class CertificateOfEmployment(models.Model):
    _name = 'certificate.of.employment'
    _description = 'Certificate of Employment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'  # Use the doc_name field as the display name

    def _get_default_approval_flow(self):
        """Get default data from approval_flow table based on the model and company."""
        try:
            _logger.info('Fetching default approval flow for model: certificate_of_employment')
            return self.env['approval.flow'].search(
                [('model_apply', '=', 'certificate_of_employment'), 
                 ('company_id', '=', self.env.company.id)],
                limit=1
            )
        except Exception as e:
            _logger.error("Error fetching default approval flow: %s", e)
            return False

    employee_certificate_id = fields.Many2one("approval.flow", string="Employee Certificate", default=_get_default_approval_flow)

    # Fields
    doc_name = fields.Char(string='Document Name', readonly=True, default='New', copy=False)
    employee = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    employee_name = fields.Char(string='Employee Name', readonly=True, compute='_compute_employee_info', store=True)
    first_name = fields.Char(string=_('First Name'), readonly=True, compute='_compute_employee_info', store=True)
    middle_name = fields.Char(string=_('Middle Name'), readonly=True, compute='_compute_employee_info', store=True)
    last_name = fields.Char(string=_('Last Name'), readonly=True, compute='_compute_employee_info', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, store=True)
    company = fields.Char(string='Company', readonly=True, compute='_compute_employee_info', store=True)
    department = fields.Char(string='Department', readonly=True, compute='_compute_employee_info', store=True)
    certified_by = fields.Many2one('hr.employee', string='Certified By', tracking=True)

    # Selection fields
    purpose = fields.Selection([
        ('Travel Abroad', 'Travel Abroad'),
        ('HMO Application', 'Application'),
        ('Meralco Application', 'Meralco Application'),
        ('Cellphone Application', 'Cellphone Application'),
        ('Renewal of Mall Entry Pass', 'Renewal of Mall Entry Pass'),
        ('Bank Loan Application', 'Bank Loan Application'),
        ('House Loan Application', 'House Loan Application'),
        ('Car/Motor Loan Application', 'Car/Motor Loan Application'),
        ('Postpaid Application', 'Postpaid Application'),
        ('Others', 'Others')
    ], string="Purpose", default='Travel Abroad', tracking=True)

    others = fields.Text(string="Others", tracking=True)
    from_date = fields.Date(string='From Date', compute='_compute_dates', store=True)
    to_date = fields.Date(string='To Date', compute='_compute_dates', store=True)
    type = fields.Selection([
        ('COE With Basic Salary & Basic Allowance', 'COE With Basic Salary & Basic Allowance'),
        ('COE With Basic Salary, Confidential Allowance and Basic Allowance', 'COE With Basic Salary, Confidential Allowance and Basic Allowance'),
        ('Without Compensation', 'Without Compensation'),
    ], string="Type", tracking=True)

    # Date fields
    posting_date = fields.Date(string='Posting Date', default=fields.Date.context_today, readonly=True)

    # Workflow setup
    is_invisible_button = fields.Boolean(string="Is Invisible Button", compute="_compute_invisible_button")
    is_approver = fields.Boolean(string="Is Approver", compute="_compute_is_approver_refuse")
    approver_id = fields.Many2one("res.users", string="Approver", store=True)
    approver_ids = fields.Many2many("res.users", string="Approver IDs", store=True)
    stage_id = fields.Many2one("movement.stage", string="Stage", compute='_compute_stage_id',
                               groups="advanced_movement.group_manager")
    current_stage_id = fields.Many2one('movement.stage', string='Current Stage', groups="advanced_movement.group_user")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('to_submit', 'Submit'),
        ('to_approve', 'To Approve'),
        ('reject', 'Rejected'),
        ('approved', 'Approved')
    ], string="Status", default="draft", required=True, readonly=True, tracking=True)

    # Automate doc_name using ir.sequence
    @api.model
    def create(self, vals):
        try:
            if vals.get('doc_name', 'New') == 'New':
                vals['doc_name'] = self.env['ir.sequence'].next_by_code('certificate.of.employment') or '/'
            return super(CertificateOfEmployment, self).create(vals)
        except Exception as e:
            _logger.error("Error creating certificate of employment: %s", e)
            raise

    # Compute employee details upon selecting Employee
    @api.depends('employee')
    def _compute_employee_info(self):
        for record in self:
            try:
                if record.employee:
                    record.employee_name = record.employee.s_full_name
                    record.department = record.employee.department_id.name
                    record.first_name = record.employee.s_first_name
                    record.middle_name = record.employee.s_middle_name
                    record.last_name = record.employee.s_last_name
                    record.company = record.employee.company_id.name
                else:
                    record.employee_name = record.department = record.company = ''
                    record.first_name = record.middle_name = record.last_name = ''
            except Exception as e:
                _logger.error("Error computing employee info for record %s: %s", record.id, e)

    @api.depends('status', 'current_stage_id.user_ids')
    def _compute_is_approver_refuse(self):
        for rec in self:
            try:
                if not rec.employee_certificate_id:
                    default_approval_flow_id = self.env['approval.flow'].search(
                        [('model_apply', '=', 'certificate_of_employment'), 
                         ('company_id', '=', rec.env.company.id)], limit=1)
                    rec.employee_certificate_id = default_approval_flow_id.id if default_approval_flow_id else False
                    if not rec.employee_certificate_id:
                        raise UserError(_("Approval Flow not set, please set it before creating a record."))

                all_stages = self.env['movement.stage'].search([('approval_flow_id', '=', rec.employee_certificate_id.id)])
                user = rec.env.user
                if rec.employee_certificate_id.sequenced:
                    rec.approver_id = user
                    rec.approver_ids = rec.current_stage_id.user_ids if rec.current_stage_id else rec.employee_certificate_id.stage_id.user_ids
                elif rec.employee_certificate_id.parallel:
                    if all([stage.status == 'pending' for stage in all_stages]):
                        rec.approver_id = user
                        rec.approver_ids = rec.employee_certificate_id.stage_id.user_ids
                    else:
                        for stage in all_stages:
                            if stage.status == 'approved':
                                if rec.approver_ids in rec.employee_certificate_id.stage_id.filtered(lambda x: x.status == 'approved').user_ids.ids:
                                    rec.approver_ids = [(3, rec.employee_certificate_id.stage_id.filtered(lambda x: x.status == 'approved').user_ids.ids)]
                            else:
                                rec.approver_ids = stage.user_ids
                rec.is_approver = not (rec.status == 'to_approve' and user in rec.approver_ids)
            except Exception as e:
                _logger.error("Error computing approver status for record %s: %s", rec.id, e)

    def action_confirm_movement(self):
        for rec in self:
            try:
                all_stages = self.env['movement.stage'].search(
                    [('approval_flow_id', '=', rec.employee_certificate_id.id), ('company_id', '=', rec.company_id.id)])
                if rec.status != 'draft':
                    raise UserError(_("You cannot approve while its status is not Draft."))
                if rec.employee_certificate_id.sequenced:
                    rec.approver_ids = rec.current_stage_id.user_ids.ids
                    self.write({'status': 'to_approve', 'current_stage_id': all_stages[0].id})
                else:
                    rec.approver_ids = rec.employee_certificate_id.stage_id.user_ids.ids
                    self.write({'status': 'to_approve'})
                    for stage in all_stages:
                        stage.write({'status': 'pending'})
                return True
            except Exception as e:
                _logger.error("Error confirming movement for record %s: %s", rec.id, e)
                raise

    def action_approved_movement(self):
        for rec in self:
            try:
                rec.approver_ids = rec.current_stage_id.user_ids.ids
                user = rec.env.user
                all_stages = self.env['movement.stage'].search([('approval_flow_id', '=', rec.employee_certificate_id.id)])
                if rec.status == 'approved':
                    raise UserError(_("This movement has already been approved."))
                if rec.status == 'reject':
                    raise UserError(_("You cannot approve a request which is in Rejected state."))
                if rec.employee_certificate_id.parallel:
                    if all(stage.status == 'approved' for stage in all_stages):
                        rec.write({'status': 'approved'})
                    else:
                        rec.write({'status': 'to_approve'})
                else:
                    if user in rec.approver_ids:
                        rec.write({'status': 'approved'})
                    else:
                        raise UserError(_("You are not an approver for this movement."))
            except Exception as e:
                _logger.error("Error approving movement for record %s: %s", rec.id, e)
                raise

    def action_reject_movement(self):
        for rec in self:
            try:
                rec.approver_ids = rec.current_stage_id.user_ids.ids
                user = rec.env.user
                if rec.status in ['approved', 'reject']:
                    raise UserError(_("You cannot reject while its status is Approved or Rejected."))
                rec.write({'status': 'reject'})
                all_stages = self.env['movement.stage'].search([('approval_flow_id', '=', rec.employee_certificate_id.id)])
                for stage in all_stages:
                    stage.write({'status': 'rejected'})
            except Exception as e:
                _logger.error("Error rejecting movement for record %s: %s", rec.id, e)
                raise

    # Method to compute the dates
    @api.depends('from_date', 'to_date')
    def _compute_dates(self):
        for record in self:
            try:
                today = date.today()
                if record.from_date and record.to_date:
                    record.from_date = record.from_date
                    record.to_date = record.to_date
                else:
                    record.from_date = today
                    record.to_date = today
            except Exception as e:
                _logger.error("Error computing dates for record %s: %s", record.id, e)

    def _compute_stage_id(self):
        for rec in self:
            try:
                if rec.employee_certificate_id:
                    rec.stage_id = self.env['movement.stage'].search([
                        ('approval_flow_id', '=', rec.employee_certificate_id.id),
                        ('company_id', '=', rec.company_id.id)
                    ])
            except Exception as e:
                _logger.error("Error computing stage ID for record %s: %s", rec.id, e)

    # Define any other necessary methods with logging
