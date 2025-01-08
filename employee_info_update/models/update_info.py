from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class UpdateInfo(models.Model):
    _name = "update.info"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Employee Info Update"
    _rec_name = 'doc_name'
   
    employee_id = fields.Many2one('hr.employee', string='Employee Name', index=True, tracking=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, store=True)
    department_id = fields.Many2one('hr.department', string='Department')
    update_date = fields.Date(string='Update Date')
    update_detail = fields.One2many('detail.update', inverse_name='update_id', string='Update Detail', required=True)
    
    reason = fields.Text(string='Reason', required=True)
    doc_name = fields.Char(string='Document Name', readonly=True, default='New', copy=False)

    """ Start of workflow setup """
    current_docstatus = fields.Integer(string="Current Docstatus", default=0)
    current_sequence = fields.Integer(string="Current Sequence", default=0)
    status = fields.Char(string="Status", tracking=True)
    can_approve = fields.Boolean(string="Can Approve", compute="_compute_can_approve_and_reject")
    # can reject - tagging if the approver has a reject button or not 
    can_reject = fields.Boolean(string="Can Reject", compute="_compute_can_approve_and_reject", store=True)
    can_cancel = fields.Boolean(string="Can Cancel", compute="_compute_can_approve_and_reject", store=True)
   
    work_flow = fields.Many2one('workflow', string='Workflow', compute='_get_workflow', store=True)

    module_approval_flow = fields.One2many(
            'update.approval.flow',
            'info_update_id',
            string='Module Approval Flow'
    )
    
    @api.model
    def open_record(self):
        """Method to explicitly trigger the can_approve calculation on record open"""
        self._compute_can_approve_and_reject()
        
    @api.model
    def _compute_can_approve_and_reject(self):
        """Compute permissions to approve, reject, or cancel based on the current user's role in the approval flow."""
        current_user_id = self.env.user.id  # Fetch the current user ID once for efficiency
        """ Use for record in self: to ensure the method works for multiple records and avoids unexpected single-record assumptions. """
        for record in self:
            # Default all permissions to False
            record.can_approve = record.can_reject = record.can_cancel = False

            # Filter relevant approvers for the current user and sequence
            relevant_approvers = record.module_approval_flow.filtered(
                lambda approver: approver.module_approver_name.id == current_user_id and
                                 approver.module_approval_sequence == record.current_sequence
            )

            # Evaluate document status for relevant approvers
            for approver in relevant_approvers:
                if approver.module_doc_status in (1, 2):
                    record.can_approve = True
                elif approver.module_doc_status == 3:
                    record.can_reject = True
                elif approver.module_doc_status == 4:
                    record.can_cancel = True
                """  break  # Exit loop after the first match """
       
            
    """ Action flow """
    def action_submit(self):
        for record in self: 
            record.current_sequence = 0
            record.current_docstatus = 0
            if record.status == 'Draft':
                record.status = 'Pending'
                record.current_sequence += 1 
                record.current_docstatus += 1
                
    def action_approve(self):
        for record in self:
            # Find the first matching approver status (if any)
            approver_status = record.module_approval_flow.filtered(
                lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status in (1, 2)
            )
           
            # If a matching approver is found, update the status and sequence
            if approver_status:
                    approver_status = approver_status[0]  # Get the first (and presumably only) matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True
                    record.current_sequence += 1      
            
            if record.current_docstatus == 2:
                employee_vals = {}
                for detail in self.update_detail:
                    employee_vals.update({detail.field_id.name: detail.new_value})
                self.employee_id.write(employee_vals)
                2

            
            
    def action_reject(self):
        for record in self:
            approver_status = record.module_approval_flow.filtered(
                        lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status == 3
                    )
        
            if approver_status:
                    approver_status = approver_status[0]  # Get the first (and presumably only) matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True

    def action_cancel(self):
        for record in self:
            approver_status = record.module_approval_flow.filtered(
                        lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status == 4
                    )
            
            if approver_status:
                    approver_status = approver_status[0]  # Get the first (and presumably only) matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True
                    
            if record.current_docstatus == 4:
                employee_vals = {}
                for detail in self.update_detail:
                    employee_vals.update({detail.field_id.name: detail.old_value})
                self.employee_id.write(employee_vals)
                2
    
    @api.depends('work_flow')
    def _populate_approval_flow(self):
        """Populate or append approval flow records for this certificate."""
        for record in self:
            if record.work_flow and record.work_flow.approvals_table:
                _logger.info("Workflow Table Record", record.work_flow.approvals_table)
                approval_values = [
                    {
                        'info_update_id': record.id,
                        'module_approver_name': approval.approver_email.id,
                        'module_approver_email': approval.approver_email.login,
                        'module_approval_status': approval.sequence_status.status_name,
                        'module_doc_status': approval.doc_status,
                        'module_approval_sequence': approval.sequence
                    }
                    for approval in record.work_flow.approvals_table
                ]

                # Bulk create missing approvals
                existing_approval_ids = self.env['update.approval.flow'].search([
                    ('info_update_id', '=', record.id),
                    ('module_approval_sequence', 'in', [approval['module_approval_sequence'] for approval in approval_values])
                ]).ids

                # Create new approvals for missing records
                missing_approvals = [approval for approval in approval_values if approval['module_approval_sequence'] not in existing_approval_ids]
                if missing_approvals:
                    self.env['update.approval.flow'].create(missing_approvals)
                    _logger.info(f"Approval flow appended for Info Update {record.id}")
                
                if not approval_values:
                    _logger.warning(f"No approval found for Info Update {record.id}")
            else:
                _logger.warning(f"No approval table found for Info Update {record.id}")

    @api.depends('employee_id')
    def _get_workflow(self):
        for record in self:
            if not record.employee_id:
                record.work_flow = False
                continue
            
            # Fetch the appropriate workflow based on conditions
            workflow = self.env['workflow'].search(
                [
                    ('companies_table.company', '=', record.company_id.id),  # Ensure 'record.company_id' references the correct field
                    ('employee_category', '=', record.employee_id.x_employeecategory_),
                    ('is_active', '=', True),
                    ('module_selection', '=', 'certificate_of_employment')
                ],
                limit=1
            )

            # Assign workflow if found
            record.work_flow = workflow.id if workflow else False

    
    """ End of workflow setup """
    
    @api.model
    def default_get(self, fields):
        res = super(UpdateInfo, self).default_get(fields)
        return res
    
    @api.model
    def write(self, vals):
        record = super(UpdateInfo, self).write(vals)
        if 'work_flow' in vals:
            self._populate_approval_flow()
        return record
    
    @api.model
    def create(self, vals):
        try:
            if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'update.info'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code)
                ], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found
            
            vals['status'] = 'Draft'  # Set status to Draft by default
            info = super(UpdateInfo, self).create(vals)
            
            if info.work_flow:
                info._populate_approval_flow()
            return info
        except Exception as e:
            _logger.error("Error creating certificate of employment: %s", e)
            raise
        
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for record in self:
            record.company_id = record.employee_id.company_id if record.employee_id else ''
            record.department_id = record.employee_id.department_id if record.employee_id else ''
            

""" Employee Info Update module approval flow """
class UpdateApprovalFlow(models.Model):
    _name = 'update.approval.flow'
    _description = 'Employee Info Approval Flow'

    info_update_id = fields.Many2one(
        'update.info',
        string='Employee Info Update',
        required=True,
        ondelete='cascade'
    )
    module_approver_name = fields.Many2one('res.users', string='Approver Name', store=True)
    module_approver_email = fields.Char(string='Approver Email', store=True)
    module_approval_status = fields.Char(string='Approval Status', store=True)
    module_approval_sequence = fields.Integer(string='Approval Sequence', store=True)
    module_doc_status = fields.Integer(string="Docstatus", store=True)
    module_approval_date =  fields.Datetime(string="Approved On")
    module_approval_confirmed = fields.Boolean(string='Confirmed Approval', store=True)

class DetailUpdate(models.Model):
    _name = "detail.update"
    _description = "Detail Update"
    
    field_name = fields.Char(string='Field Name')
    field_id = fields.Many2one('ir.model.fields', string='Field ID', domain="[('model_id.model', '=', 'hr.employee')]")
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')
    update_id = fields.Many2one('update.info', string='Update ID')
    
    @api.onchange('field_id')
    def onchange_field_name(self):
        if self.field_id:
            self.old_value = getattr(self.update_id.employee_id, self.field_id.name)
            
            