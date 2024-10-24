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
        """ get default data from approval_flow table """
        return self.env['approval.flow'].search([('model_apply', '=', 'certificate_of_employment'), ('company_id', '=', self.env.company.id)], limit=1)

    # linked to table approval flow like fk between table certificate_of_employment and approval_flow table
    employee_certificate_id = fields.Many2one("approval.flow", string="Employee Certificate", default=_get_default_approval_flow)

    # Fields
    doc_name = fields.Char(string='Document Name', readonly=True, default='New', copy=False)  # Define doc_name
    employee = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    employee_name = fields.Char(string='Employee Name', readonly=True, compute='_compute_employee_info', store=True)
    first_name = fields.Char(string=_('First Name'), readonly=True, compute='_compute_employee_info', store=True)
    middle_name = fields.Char(string=_('Middle Name'), readonly=True, compute='_compute_employee_info', store=True)
    last_name = fields.Char(string=_('Last Name'), readonly=True, compute='_compute_employee_info', store=True)
    company_id = fields.Char(string='Company', readonly=True, compute='_compute_employee_info', store=True)
    department = fields.Char(string='Department', readonly=True, compute='_compute_employee_info', store=True)
   # employment_status = fields.Char(string=_('Employment Status'), readonly=True, compute='_compute_employee_info', store=True)
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
    
    
    """ Workflow setup """
    is_invisible_button = fields.Boolean(string="Is Invisible Button", compute="_compute_invisible_button")
    is_approver = fields.Boolean(string="Is Approver", compute="_compute_is_approver_refuse")
    approver_id = fields.Many2one("res.users", string="Approver", store=True)
    approver_ids = fields.Many2many("res.users", string="Approver IDs", store=True)
    stage_id = fields.Many2one("movement.stage", string="Stage", compute='_compute_stage_id',
                               groups="advanced_movement.group_manager")
    current_stage_id = fields.Many2one('movement.stage', string='Current Stage',
                                       groups="advanced_movement.group_user")
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
        if vals.get('doc_name', 'New') == 'New':
            vals['doc_name'] = self.env['ir.sequence'].next_by_code('certificate.of.employment') or '/'
        return super(CertificateOfEmployment, self).create(vals)

    # Compute employee details upon selecting Employee
    @api.depends('employee')
    def _compute_employee_info(self):
        for record in self:
            if record.employee:
                record.employee_name = record.employee.s_full_name
                record.department = record.employee.department_id.name
                record.company_id = record.employee.company_id.name
                record.first_name = record.employee.s_first_name
                record.middle_name = record.employee.s_middle_name
                record.last_name = record.employee.s_last_name
               # record.employment_status = record.employee.employment_status
            else:
                record.employee_name = record.department = record.company_id = ''
                record.first_name = record.middle_name = record.last_name = ''
               # record.employment_status = ''
               
               
    '''---------------------Apply Approval Flow for button---------------------'''

    @api.depends('status', 'current_stage_id.user_ids')
    def _compute_is_approver_refuse(self):
        '''This function aim to invisible or display button approve by user have permission approve approval flow'''
        for rec in self:
            if not rec.employee_certificate_id:
                default_approval_flow_id = self.env['approval.flow'].search([('model_apply', '=', 'certificate_of_employment'), ('company_id', '=', rec.env.company.id)], limit=1)
                rec.employee_certificate_id = default_approval_flow_id.id if default_approval_flow_id else False
                if not rec.employee_certificate_id:
                    raise UserError(_("Approval Flow not setting ,please setting before create record."))


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
            if rec.status == 'to_approve' and user in rec.approver_ids:
                rec.is_approver = False
            else:
                rec.is_approver = True

    def action_confirm_movement(self):
        for rec in self:
            all_stages = self.env['movement.stage'].search(
                [('approval_flow_id', '=', rec.employee_certificate_id.id), ('company_id', '=', rec.company_id.id)])
            print('all_stages', all_stages)
            if rec.status != 'draft':
                raise UserError(_("You can not approve while its status is not Draft."))
        if rec.employee_certificate_id.sequenced:
            rec.approver_ids = rec.current_stage_id.user_ids.ids
            self.write({'status': 'to_approve', 'current_stage_id': all_stages[0].id})
        else:
            rec.approver_ids = rec.employee_certificate_id.stage_id.user_ids.ids
            self.write({'status': 'to_approve'})
            for rec in all_stages:
                rec.write({'status': 'pending'})
        return True

    # Workflow Setup
    def action_approved_movement(self):
        for rec in self:
            rec.approver_ids = rec.current_stage_id.user_ids.ids
            user = rec.env.user
            all_stages = self.env['movement.stage'].search([('approval_flow_id', '=', rec.employee_certificate_id.id)])
            if rec.status == 'approved':
                raise UserError(_("This movement has already been approved."))
            if rec.status == 'reject':
                raise UserError(_("You cannot approve a request which is in Rejected state."))
            if rec.employee_certificate_id.parallel:
                all_stages = self.env['movement.stage'].search(
                    [('approval_flow_id', '=', rec.employee_certificate_id.id)])
                user = rec.env.user
                current_actions_stages = all_stages.filtered(lambda rec: rec.status != 'approved')
                if user in current_actions_stages.user_ids:
                    for stage in current_actions_stages:
                        if user in stage.user_ids:
                            rec.write({'current_stage_id': stage.id})
                            stage.write({'status': 'approved'})
                            rec.message_post(
                                body=_("%s has approved  %s.") % (user.name, stage.name),
                                message_type='notification',
                                subtype_xmlid='mail.mt_comment'
                            )
                            break
                if all([status == 'approved' for status in all_stages.mapped('status')]):
                    rec.with_context(button_action=True).write({'status': 'approved'})
                    all_stages.write({'status': 'pending'})

            else:
                before_action_stages = rec.current_stage_id
                current_actions_stages = all_stages.filtered(lambda x: x.sequence > (before_action_stages.sequence - 1))
                if current_actions_stages and user in current_actions_stages[0].user_ids:
                    for stage in current_actions_stages.sorted(key=lambda x: x.sequence):
                        next_stage = current_actions_stages.filtered(lambda x: x.sequence > stage.sequence)
                        if next_stage:
                            rec.write({'current_stage_id': next_stage[0].id})
                            rec.message_post(
                                body=_("%s has approved  %s.") % (user.name, stage.name),
                                message_type='notification',
                                subtype_xmlid='mail.mt_comment'
                            )
                            break
                        else:
                            rec.with_context(button_action=True).write({'status': 'approved'})


