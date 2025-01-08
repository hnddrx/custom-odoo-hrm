import random
import string
from odoo import fields, models, api
from datetime import date
import logging
import psycopg2
import urllib.parse  # Import urllib.parse for URL encoding

_logger = logging.getLogger(__name__)

class DisciplinaryAction(models.Model):
    _name = "disciplinary.action"
    _description = "Disciplinary Action"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'
    
    
    doc_name = fields.Char(string="Name", readonly=True, default='New')
    
    # Many2one relationship field
    incident_report = fields.Many2one('incident.report', string='Incident Report',required=True)
    
    sanction = fields.Many2one('sanction.lists', string='Sanction', required=True)
    description = fields.Char(string='Sanction Description', readonly=True, compute='_get_sanction', store=True)
    next_sanction = fields.Many2one('sanction.lists', string='Next Sanction')
    next_sanction_description = fields.Char(string='Sanction Description', readonyl=True, compute='_get_sanction', store=True)
    underwent_preventive_suspension = fields.Boolean(string="Underwent to Preventive Suspension", default=False)
    underwent = fields.Boolean(string='Underwent to a conference', default=False)
    offense = fields.Many2one('offense.lists', string='Offense',required=True)
    offense_description = fields.Char(string='Offense Description', readonly=True, compute='_get_offense', store=True)
    
    terminated_on = fields.Date(string='Terminated On')

    employee = fields.Many2one('hr.employee',string='Employee', required=True)
    employee_name = fields.Char(string='Employee Number', readonly=True, compute='_compute_employee_info', store=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, compute="_compute_employee_info", store=True)
    department = fields.Char(string='Department', readonly=True, compute = '_compute_employee_info', store=True)
    branch = fields.Char(string='Branch', readonly=True, compute = '_compute_employee_info', store=True )
    brand = fields.Char(string="Brand", readonly=True, compute = '_compute_employee_info', store=True )
    number_of_days = fields.Integer(string='Number of Suspension Days')
    posting_date = fields.Date(string='Posting Date', default=fields.Date.context_today, readonly=True)
    suspended_from = fields.Date(string='Suspended From')
    suspended_to = fields.Date(string='Suspended To')
    employee_category = fields.Char(string="Employee Category", readonly=True, compute="_compute_employee_info",store=True)
    
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        string="Attachments", 
        help="Attachments related to this document"
    )

    
    #Text fields
    hearing_remarks = fields.Text(string='Hearing Remarks')
    remarks = fields.Text(string='Remarks')
    report_url = fields.Char(string="Report URL", compute="_compute_report_url", store=True)
    
    """ Put needed workflow fields """
    
    # Workflow
    current_docstatus = fields.Integer(string="Current Docstatus", default=0)
    current_sequence = fields.Integer(string="Current Sequence", default=0)
    status = fields.Char(string="Status", tracking=True)
    can_approve = fields.Boolean(string="Can Approve", compute="_compute_can_approve_and_reject")
    # can reject - tagging if the approver has a reject button or not 
    can_reject = fields.Boolean(string="Can Reject", compute="_compute_can_approve_and_reject", store=True)
    can_cancel = fields.Boolean(string="Can Cancel", compute="_compute_can_approve_and_reject", store=True)

    work_flow = fields.Many2one('workflow', string='Workflow', compute='_get_workflow', store=True)
    
    module_approval_flow = fields.One2many(
        'disciplinary.approval.flow',
        'disciplinary_id',
        string='Module Approval Flow'
    )
    
    """ End of workflow fild """
    
    """ put workflow logic here """
    
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
                    
    @api.depends('work_flow')
    def _populate_approval_flow(self):
        """Populate or append approval flow records for this certificate."""
        for record in self:
            if record.work_flow and record.work_flow.approvals_table:
                approval_values = [
                    {
                        'disciplinary_id': record.id,
                        'module_approver_name': approval.approver_email.id,
                        'module_approver_email': approval.approver_email.login,
                        'module_approval_status': approval.sequence_status.status_name,
                        'module_doc_status': approval.doc_status,
                        'module_approval_sequence': approval.sequence
                    }
                    for approval in record.work_flow.approvals_table
                ]

                # Bulk create missing approvals
                existing_approval_ids = self.env['disciplinary.approval.flow'].search([
                    ('disciplinary_id', '=', record.id),
                    ('module_approval_sequence', 'in', [approval['module_approval_sequence'] for approval in approval_values])
                ]).ids

                # Create new approvals for missing records
                missing_approvals = [approval for approval in approval_values if approval['module_approval_sequence'] not in existing_approval_ids]
                if missing_approvals:
                    self.env['disciplinary.approval.flow'].create(missing_approvals)
                    _logger.info(f"Approval flow appended for certificate {record.id}")
                
                if not approval_values:
                    _logger.warning(f"No approval found for certificate {record.id}")
            else:
                _logger.warning(f"No approval table found for certificate {record.id}")
                
    @api.depends('employee')    
    def _get_workflow(self):
        """Compute and assign the appropriate workflow based on the employee's company."""
        for record in self:
            if not record.employee:
                record.work_flow = False
                continue
            
            # Fetch the appropriate workflow based on conditions
            workflow = self.env['workflow'].search(
                [
                    ('companies_table.company', '=', record.company_id.id),  # Ensure 'record.company_id' references the correct field
                    ('employee_category', '=', record.employee_category),
                    ('is_active', '=', True),
                    ('module_selection', '=', 'disciplinary_action')
                ],
                limit=1
            )

            # Assign workflow if found
            record.work_flow = workflow.id if workflow else False

    
    """ End of workflow """
    
    """ Generate jasper report """
    def _compute_report_url(self):
        """Private method to compute the report URL."""
        for record in self:
            base_url = 'http://192.168.2.161:8080/jasperserver/flow.html'
            params = {
                '_flowId': 'viewReportFlow',
                'ParentFolderUri': '/Forms',
                'reportUnit': '/forms/notice_of_decision',
                'standAlone': 'true',
                'j_username': 'jasperadmin',
                'j_password': 'jasperadmin',
                'output': 'pdf',
                'filter1': record.doc_name or ''
            }
            # Construct the full URL with query parameters
            record.report_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    def action_generate_report_url(self):
        """Public method to be called by the button."""
        self._compute_report_url()
        # Optionally return an action or response
        return {
            'type': 'ir.actions.act_url',
            'url': self.report_url,
            'target': 'new',  # Opens in a new tab
        }
        
    """ End Generate Report  """   
    
    
    @api.model
    def create(self, vals):
        try:
            if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'disciplinary.action'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code)
                ], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found
            
            """ Important for workflow setup """
            vals['status'] = 'Draft'  # Set status to Draft by default 
            disciplinary_action = super(DisciplinaryAction, self).create(vals)
            
            if disciplinary_action.work_flow:
                disciplinary_action._populate_approval_flow()
            return disciplinary_action
        except Exception as e: 
            _logger.error("Error creating certificate of employment: %s", e)
            raise

    """   @api.depends('incident_report')
    def _compute_offense(self):
        for record in self:
            record.incident_report_description = record.offense.description if record.offense else ''
            
            """ 
    @api.depends('employee')
    def _compute_employee_info(self):
        for record in self:
            employee = record.employee
            if employee:
                record.employee_name = employee.s_employee_id
                record.department = employee.department_id.name
                record.branch = employee.x_branch
                record.brand = employee.x_brand_
                record.employee_category = record.employee.x_employeecategory_
                record.company_id = record.employee.company_id.id                

            else:
                record.employee_name = ''
                record.department = ''
                record.branch = ''
                record.brand = ''
                record.employee_category = ''
                record.company_id = ''
            
    @api.depends('sanction','next_sanction')
    def _get_sanction(self):
        for record in self:
            record.description = record.sanction.description if record.sanction else ''
            record.next_sanction_description = record.next_sanction.description if record.next_sanction else ''
            
    @api.depends('offense')
    def _get_offense(self):
        for record in self:
            record.offense_description = record.offense.description if record.offense else '' 


class DisciplinaryApprovalFlow(models.Model):
    _name = 'disciplinary.approval.flow'
    _description = 'Disciplinary Approval Flow'

    disciplinary_id = fields.Many2one(
        'disciplinary.action',
        string='Disciplinary Action',
        ondelete='cascade'
    )
    module_approver_name = fields.Many2one('res.users', string='Approver Name', store=True)
    module_approver_email = fields.Char(string='Approver Email', store=True)
    module_approval_status = fields.Char(string='Approval Status', store=True)
    module_approval_sequence = fields.Integer(string='Approval Sequence', store=True)
    module_doc_status = fields.Integer(string="Docstatus", store=True)
    module_approval_date =  fields.Datetime(string="Approved On")
    module_approval_confirmed = fields.Boolean(string='Confirmed Approval', store=True)
