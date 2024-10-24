from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CertificateOfEmployment(models.Model):
    _name = 'certificate.of.employment'
    _description = 'Certificate of Employment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'  # Use the doc_name field as the display name

    # Fields
    doc_name = fields.Char(string='Document Name', readonly=True, default='New', copy=False)  # Define doc_name
    employee = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    employee_name = fields.Char(string='Employee Name', readonly=True, compute='_compute_employee_info', store=True)
    first_name = fields.Char(string=_('First Name'), readonly=True, compute='_compute_employee_info', store=True)
    middle_name = fields.Char(string=_('Middle Name'), readonly=True, compute='_compute_employee_info', store=True)
    last_name = fields.Char(string=_('Last Name'), readonly=True, compute='_compute_employee_info', store=True)
    company = fields.Char(string='Company', readonly=True, compute='_compute_employee_info', store=True)
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
                record.company = record.employee.company_id.name
                record.first_name = record.employee.s_first_name
                record.middle_name = record.employee.s_middle_name
                record.last_name = record.employee.s_last_name
               # record.employment_status = record.employee.employment_status
            else:
                record.employee_name = record.department = record.company = ''
                record.first_name = record.middle_name = record.last_name = ''
               # record.employment_status = ''
