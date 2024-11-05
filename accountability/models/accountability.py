from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class EmployeeAccountability(models.Model):
    _name = 'accountability'
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

    department = fields.Char(string='Department', readonly=True, compute='_compute_employee_info', store=True)
    company = fields.Char(string='Company', readonly=True, compute='_compute_employee_info', store=True)

    posting_date = fields.Date(string='Posting Date', default=fields.Date.today)
    accountability_type = fields.Selection([
        ('issuance', 'Issuance'),
        ('return', 'Return'),
    ], string='Type', required=True, default='issuance')
    
    issuance_table = fields.One2many(
        'issuance',
        'accountability_id',
        string = 'Issuance Table'
        
    )
    
    return_table = fields.One2many(
        'return',
        'accountability_id',
        string = 'Return Table'
        
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

class Issuance(models.Model):
    _name = 'issuance'
    _description = 'Issuance'
    
    
    accountability_id = fields.Many2one('accountability', string="Accountability ID")
    item_name = fields.Char(string="Item Name")
    item_code = fields.Char(string="Item Code")
    quantity = fields.Integer(string="Quantity")
    date_issued = fields.Date(string="Date Issued")
    
class Return(models.Model):
    _name = 'return'
    _description = 'Return'
    
    
    accountability_id = fields.Many2one('accountability', string="Accountability ID")
    item_name = fields.Char(string="Item Name")
    item_code = fields.Char(string="Item Code")
    quantity = fields.Integer(string="Quantity")
    date_issued = fields.Date(string="Date Issued") 
    return_to = fields.Many2one('hr.employee', string='Return To')
    date_returned = fields.Date( string='Date Returned')
    
