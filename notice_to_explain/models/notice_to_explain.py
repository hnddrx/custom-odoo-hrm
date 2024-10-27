import random
import string
from odoo import fields, models, api, _
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class NoticeToExplain(models.Model):
    _name = "notice.to.explain"
    _description = "Notice to Explain"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'
    
    doc_name = fields.Char(string="Name", readonly=True, default='New')
    
    # Many2one relationship field
    incident_report = fields.Many2one('incident.report', string=_('Incident Report'),required=True)
    """  incident_report_description = fields.Text(string='Description', readonly=True) """
    

    employee = fields.Many2one('hr.employee',string=_('Employee'), required=True)
    employee_name = fields.Char(string=_('Employee Name'), readonly=True, compute='_compute_employee_name', store=True)
    
    attachment = fields.Binary(string="Attachment")
    attachment_filename = fields.Char(string="Attachment Filename")

    remarks = fields.Text(string=_("Remarks"))
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted')
    ], string="Status", default='draft', tracking=True)
    
    @api.model
    def create(self, vals):
        """Generate document name sequence during creation."""
        if vals.get('doc_name', 'New') == 'New':
            vals['doc_name'] = self.env['ir.sequence'].next_by_code('notice.to.explain') or 'New'
        return super(NoticeToExplain, self).create(vals)
    
    
    # Button action to submit the form
    def action_submit(self):
        self.write({'status': 'submitted'})

    # Button to reset to draft (for example, if rejected)
    def action_reset_draft(self):
        self.write({'status': 'draft'})

    
    