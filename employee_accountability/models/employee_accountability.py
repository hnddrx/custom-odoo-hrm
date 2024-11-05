from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class EmployeeAccountability(models.Model):
    _name = 'employee.accountability'
    _description = 'Employee Accountability'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'

    # Fields
    doc_name = fields.Char(string="Document Name", readonly=True, default='New', copy=False)

    employee = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        context={'no_create': True}  # This prevents creating new employees
    )
    first_name = fields.Char(string="First Name", readonly=True, compute='_compute_employee_info', store=True)
    last_name = fields.Char(string="Last Name", readonly=True, compute='_compute_employee_info', store=True)
    form_items = fields.One2many('dynamic.form.item', 'main_id', string='Form Items')

    department = fields.Char(string='Department', readonly=True, compute='_compute_employee_info', store=True)
    company = fields.Char(string='Company', readonly=True, compute='_compute_employee_info', store=True)

    posting_date = fields.Date(string='Posting Date', default=fields.Date.today)
    accountability_type = fields.Selection([
        ('issuance', 'Issuance'),
        ('return', 'Return'),
    ], string='Type', required=True, default='issuance')

    # Override create method
    @api.model
    def create(self, vals):
        if vals.get('doc_name', 'New') == 'New':
            vals['doc_name'] = self.env['ir.sequence'].next_by_code('employee.accountability') or 'New'

        # Call the super method to create the record
        record = super(EmployeeAccountability, self).create(vals)

        # Fetch employee data if employee is present
        if record.employee:
            record.company = record.employee.company_id.name
            record.department = record.employee.department_id.name

        return record

    # Compute employee details upon selecting Employee
    @api.depends('employee')
    def _compute_employee_info(self):
        for record in self:
            if record.employee:
                record.department = record.employee.department_id.name
                record.company = record.employee.company_id.name
                record.first_name = record.employee.s_first_name
                record.last_name = record.employee.s_last_name
            else:
                record.department = ''
                record.company = ''
                record.first_name = ''
                record.last_name = ''

    # @api.onchange('accountability_type')
    # def _onchange_accountability_type(self):
    #     for record in self:
    #         # Set the domain for form_items based on accountability_type
    #         if record.accountability_type == 'issuance':
    #             domain = [('issuance', '=', True)]
    #             # Resetting specific fields in form_items
    #             for item in record.form_items:
    #                 item.return_to = False
    #                 item.date_return = False
    #                 item.date_issue = False  # Resetting date_issue if needed
    #                 item.return_to_invi = True
    #                 item.date_return_invi = True
    #                 item.date_issued_invi = True
    #         elif record.accountability_type == 'return':
    #             domain = [('return', '=', True)]
    #             # Resetting specific fields in form_items
    #             for item in record.form_items:
    #                 item.return_to = False
    #                 item.date_return = False
    #                 item.date_issue = False  # Resetting date_issue if needed
    #                 item.return_to_invi = False
    #                 item.date_return_invi = False
    #                 item.date_issued_invi = False
    #         else:
    #             domain = []  # No specific domain if no accountability type is selected

    #     # Return the domain to filter the form_items accordingly
    #     return {'domain': {'form_items': domain}}

    @api.onchange('accountability_type')
    def _onchange_accountability_type(self):
        for record in self:
            domain = []
            for item in record.form_items:
                # Reset fields for both issuance and return
                item.return_to = False
                item.date_return = False
                item.date_issue = False

                if record.accountability_type == 'issuance':
                    domain = [('issuance', '=', True)]
                    # Set visibility fields for issuance
                    item.return_to_invi = True
                    item.date_return_invi = True
                    item.date_issued_invi = True
                elif record.accountability_type == 'return':
                    domain = [('return', '=', True)]
                    # Set visibility fields for return
                    item.return_to_invi = False
                    item.date_return_invi = False
                    item.date_issued_invi = False

        # Return the domain to filter the form_items accordingly
        return {'domain': {'form_items': domain}}



class DynamicFormItem(models.Model):
    _name = 'dynamic.form.item'
    _description = 'Dynamic Form Item'

    main_id = fields.Many2one('employee.accountability', string='ID', ondelete='cascade')
    accountability_type_rel = fields.Selection(related='main_id.accountability_type', string='Type', store=True)
    item_name = fields.Char(string='Item Name', required=True)
    item_code = fields.Char(string='Item Code')
    quantity = fields.Integer(string='Quantity', default=1)
    date_issue = fields.Date(string='Date Issued', default=fields.Date.today)
    return_to = fields.Char(string="Return To")
    date_return = fields.Date(string='Date Returned')

    return_to_invi = fields.Boolean(default=True)
    date_return_invi = fields.Boolean(default=True)
    date_issued_invi = fields.Boolean(default=True)
