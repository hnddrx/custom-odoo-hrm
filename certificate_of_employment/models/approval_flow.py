from odoo import fields, models, _

class ApprovalFlow(models.Model):
    _inherit = 'approval.flow'

    def _get_selection_options(self):

        # Get the existing options from the parent method
        options = super(ApprovalFlow, self)._get_selection_options()

        # Define the options to return when default_selection matches
        options.append(('certificate_of_employment', 'Certificate of Employment'))

        return options

    model_apply = fields.Selection(selection='_get_selection_options', string=_("Module Applied"), required=True)