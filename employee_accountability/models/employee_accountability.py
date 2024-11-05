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
    
    issuance_table = fields.One2many(
        'issuance.table',
        'employee_accountability_id',
        string='Issuance'
    )
    
    return_table = fields.One2many(
        'return.table',
        'employee_accountability_id',
        string='Return'
    )

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


class IssuanceTable(models.Model):
    _name = "issuance.table"
    _description = "Issuance Table"
    
    employee_accountability_id = fields.Many2one('employee.accountability', string="Employee Accountability")
    item_name = fields.Char(string="Item Name", required=True)
    item_code = fields.Char(string="Item Code", required=True)  # Fixed typo here
    quantity = fields.Integer(string="Quantity") 
    date_issued = fields.Date(string="Date Issued")
    
class ReturnTable(models.Model):
    _name = "return.table"
    _description = "Return Table"
    
    employee_accountability_id = fields.Many2one('employee.accountability', string="Employee Accountability")
    item_name = fields.Char(string="Item Name", required=True)
    item_code = fields.Char(string="Item Code", required=True)  # Fixed typo here
    quantity = fields.Integer(string="Quantity") 
    date_issued = fields.Date(string="Date Issued")
    return_to = fields.Many2one('hr.employee', string="Return To", required=True)
    date_returned = fields.Date(string="Date Returned", required=True)
    