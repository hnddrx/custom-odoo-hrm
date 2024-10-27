from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class EmployeeMedicalRecords(models.Model):
    _name = 'employee.medical.record'
    _description = 'Employee Medical Records'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'
    
    # Fields
    doc_name = fields.Char(string='Document Name', readonly=True, default='New', copy=False)
    employee = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    posting_date = fields.Date(string='Posting Date', default=fields.Date.context_today, readonly=True)
    date = fields.Date(string='Date', required=True, tracking=True)
    
    first_name = fields.Char(string='First Name', readonly=True, copy=False)
    middle_name = fields.Char(string='Middle Name', readonly=True, copy=False)
    last_name = fields.Char(string='Last Name', readonly=True, copy=False)
    
    medical_type = fields.Many2one('medical.type', string='Medical Type', required=True)
    other_type = fields.Text(string='Other Type')
    
    # New boolean field to control visibility
    show_other_type = fields.Boolean(string="Show Other Type", compute="_compute_show_other_type")

    # Duration fields
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    existing_condition = fields.Text(string='Existing Condition')
    other_remarks = fields.Text(string='Other Remarks')
    
    # File Upload Zone
    file_data = fields.Binary(string="File", copy=False)
    file_name = fields.Char(string="File Name", copy=False)

    @api.model
    def create(self, vals):
        # Generate sequence for the document name
        if vals.get('doc_name', 'New') == 'New':
            vals['doc_name'] = self.env['ir.sequence'].next_by_code('employee.medical.records') or 'New'
        return super(EmployeeMedicalRecords, self).create(vals)

    @api.depends('medical_type')
    def _compute_show_other_type(self):
        """ Show the 'Other Type' field only if the selected medical type is 'Others (Please Specify)' """
        others_type_name = "Others (Please Specify)"
        for record in self:
            if record.medical_type and record.medical_type.name == others_type_name:
              
                record.show_other_type = True
                _logger.info('Show Other Type',record.show_other_type)
            else:
                record.show_other_type = False
                _logger.info('Show Other Type',record.show_other_type)
                
