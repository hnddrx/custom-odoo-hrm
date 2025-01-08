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
    
    first_name = fields.Char(string='First Name', readonly=True, compute="_get_employee_info", copy=False)
    middle_name = fields.Char(string='Middle Name', readonly=True, compute="_get_employee_info", copy=False)
    last_name = fields.Char(string='Last Name', readonly=True, compute="_get_employee_info", copy=False)
    gender = fields.Char(string="Gender", readonly=True, compute="_get_employee_info", copy=False)
    
    company = fields.Char(string='Company', readonly=True, compute="_get_employee_info", copy=False)
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
    
    """ Selection fields here """
    
    separation = fields.Selection([
        ('pre_placement', 'Pre Placement'),
        ('periodic', 'Periodic'),
        ('return_to_work', 'Return to Work'),
        ('transfer', 'Transfer'),
        ('special', 'Special'),
        ('separation', 'Separation'),
        ]
        ,string="Separation"
    )
    
    special = fields.Selection([
        ('pre_placement', 'Pre Placement'),
        ('periodic', 'Periodic'),
        ('return_to_work', 'Return to Work'),
        ('transfer', 'Transfer'),
        ('special', 'Special'),
        ('separation', 'Separation'),
        ]
        ,string="Special"
    )
    
    transfer = fields.Selection([
        ('pre_placement', 'Pre Placement'),
        ('periodic', 'Periodic'),
        ('return_to_work', 'Return to Work'),
        ('transfer', 'Transfer'),
        ('special', 'Special'),
        ('separation', 'Separation'),
        ]
        ,string="Transfer"
    )
    
    
    pre_placement = fields.Selection([
        ('physical_exam', 'Physical Exam'),
        ('x_rays', 'X-Rays'),
        ('urinalysis', 'Urinalysis'),
        ('stool_exam', 'Stool Exam'),
        ('ecg', 'ECG'),
        ('others', 'Others, Specify'),
        ]
        ,string="Pre Placement"
    )
    
    return_to_work = fields.Selection([
        ('physical_exam', 'Physical Exam'),
        ('x_rays', 'X-Rays'),
        ('urinalysis', 'Urinalysis'),
        ('stool_exam', 'Stool Exam'),
        ('ecg', 'ECG'),
        ('others', 'Others, Specify'),
        ]
        ,string="Return to Work"
    )
    
    periodic = fields.Selection([
        ('physical_exam', 'Physical Exam'),
        ('x_rays', 'X-Rays'),
        ('urinalysis', 'Urinalysis'),
        ('stool_exam', 'Stool Exam'),
        ('ecg', 'ECG'),
        ('others', 'Others, Specify'),
        ]
        ,string="Periodic"
    )
    
    
    diseases_skin = fields.Selection([
        ('allergy', 'Allergy'),
        ('dermatoses', 'Dermatoses'),
        ('infection', 'Infection as folliculitis abscess/paranychia'),
        ('others', 'Others'),
        ],
        string="Diseases (Skin)"
    )
    
    diseases_head = fields.Selection([
        ('tension_headache', 'Tension/Headache'),
        ('others', 'Others, specify'),
        ],
        string="Diseases (Head)"
    )
    
    diseases_eyes = fields.Selection([
        ('gingivitis', 'Gingivitis'),
        ('herpes_labiales_nasalis',  'Herpes Labiales/Nasalis'),
        ('otitis_media_externa', 'Otitis Media Externa'),
        ('deafness', 'Deafness'),
        ('meniere_syndrome_vertigo', 'Meniere”s Syndrome /Vertigo'),
        ('rhinitis', 'Rhinitis'),
        ('nasal_polyps', 'Nasal Polyps'),
        ('sinusitis', 'Sinusitis'),
        ('tonsilio_pharyngitis', 'Tonsilio pharyngitis'),
        ('laryngitis', 'Laryngitis'),
        ('others', 'Others, specify'),
        ],
        string="Diseases (Eyes)"
    )
    
    # Mouth & ENT
    mouth_ent_condition = fields.Selection([
        ('gingivitis', 'Gingivitis'),
        ('herpes_labiales', 'Herpes Labiales/ Nasalis'),
        ('otitis_media', 'Otitis Media Externa'),
        ('deafness', 'Deafness'),
        ('menieres_syndrome', 'Meniere’s Syndrome /Vertigo'),
        ('rhinitis_colds', 'Rhinitis/Colds'),
        ('nasal_polyps', 'Nasal Polyps'),
        ('sinusitis', 'Sinusitis'),
        ('tonsilio_pharyngitis', 'Tonsilio Pharyngitis'),
        ('laryngitis', 'Laryngitis'),
        ('others', 'Others')
    ], string="Mouth & ENT Condition")

    # Respiratory
    respiratory_condition = fields.Selection([
        ('bronchitis', 'Bronchitis'),
        ('bronchial_asthma', 'Bronchial/Asthma'),
        ('pneumonia', 'Pneumonia'),
        ('tuberculosis', 'Tuberculosis'),
        ('pneumoconiosis', 'Pneumoconiosis'),
        ('others', 'Others')
    ], string="Respiratory Condition")

    # Heart and Blood Vessel
    heart_blood_vessel_condition = fields.Selection([
        ('hypertension', 'Hypertension'),
        ('hypotension', 'Hypotension'),
        ('angina_pectoris', 'Angina Pectoris'),
        ('myocardial_infarction', 'Myocardial Infarction'),
        ('vascular_disturbances', 'Vascular disturbances in extremities due to continuous vibration'),
        ('others', 'Others')
    ], string="Heart and Blood Vessel Condition")

    # Gastrointestinal
    gastrointestinal_condition = fields.Selection([
        ('gastroenteritis', 'Gastroenteritis/ Diarrhea'),
        ('amoebiasis', 'Amoebiasis'),
        ('gastritis', 'Gastritis/ Hyperacidity'),
        ('appendicitis', 'Appendicitis'),
        ('infectious_hepatitis', 'Infectious Hepatitis'),
        ('liver_cirrhosis', 'Liver Cirrhosis'),
        ('hepatic_abscess', 'Hepatic Abscess'),
        ('cancer_hepatic_gastric', 'Cancer (Hepatic/ Gastric)'),
        ('ulcer', 'Ulcer'),
        ('others', 'Others')
    ], string="Gastrointestinal Condition")

    # Genito Urinary
    genito_urinary_condition = fields.Selection([
        ('urinary_tract_infection', 'Urinary Tract infection'),
        ('stones', 'Stones'),
        ('cancer', 'Cancer'),
        ('others', 'Others')
    ], string="Genito Urinary Condition")

    # Reproductive
    reproductive_condition = fields.Selection([
        ('dysmenorrhea', 'Dysmenorrhea'),
        ('infection_cervicitis', 'Infection (Cervicitis) (Vaginitis)'),
        ('abortion_spontaneous', 'Abortion (Spontaneous)'),
        ('abortion_threatened', 'Abortion (Threatened)'),
        ('hyperemesis_gravidarum', 'Hyperemesis Gravidarum'),
        ('uterine_tumors', 'Uterine Tumors'),
        ('cervical_polyp_cancer', 'Cervical Polyp/Cancer')
    ], string="Reproductive Condition")

    # Immunization Program
    immunization_program = fields.Selection([
        ('tetanus_toxoid_injection', 'Tetanus Toxoid Injection'),
        ('tetanus_antioxin_injection', 'Tetanus Antioxin Injection'),
        ('tetanus_globulin_injection', 'Tetanus Globulin Injection'),
        ('hepatitis_b_vaccine', 'Hepatitis B Vaccine'),
        ('rabies_vaccine', 'Rabies Vaccine'),
        ('others', 'Others (Please Specify)')
    ], string="Immunization Program")

    # Chemical Hazard
    chemical_hazard = fields.Selection([
        ('dust', 'Dust (Ex. Silica dust)'),
        ('liquid', 'Liquid (Ex. Mercury)'),
        ('mist_fumes_vapors', 'Mist/fumes/vapors (Ex. mist from paint spraying)'),
        ('gas', 'Gas (Ex. CO, H2S)'),
        ('others', 'Others (please specify)')
    ], string="Chemical Hazard")

    # Physical Hazards
    physical_hazards = fields.Selection([
        ('noise', 'Noise'),
        ('temperature_humidity', 'Temperature/humidity'),
        ('pressure', 'Pressure'),
        ('illumination', 'Illumination'),
        ('radiation', 'Radiation/ultraviolet/microwave'),
        ('vibration', 'Vibration'),
        ('others', 'Others (Please specify)')
    ], string="Physical Hazards")

    # Biological hazard
    biological_hazard = fields.Selection([
        ('viral', 'Viral'),
        ('bacterial', 'Bacterial'),
        ('fungal', 'Fungal'),
        ('parasitic', 'Parasitic'),
        ('others', 'Others, specify')
    ], string="Biological Hazard")

    # Ergonomic Stress
    ergonomic_stress = fields.Selection([
        ('exhausting_physical_work', 'Exhausting physical work'),
        ('prolonged_standing', 'Prolonged standing'),
        ('low_back_pain', 'Low back pain'),
        ('unfavorable_work_posture', 'Unfavorable work posture'),
        ('static_monotonous_work', 'Static/monotonous work'),
        ('others', 'Others, specify')
    ], string="Ergonomic Stress")
    
    
    """ End of selection fields """

    @api.model
    def create(self, vals):
        if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'employee.medical.record'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code)
                ], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found
        return super(EmployeeMedicalRecords, self).create(vals)
    
    
    @api.depends('employee')
    def _get_employee_info(self):
        """ Get employee information """
        for record in self:
            record.first_name = record.employee.s_first_name if record.employee else ''
            record.middle_name = record.employee.s_middle_name if record.employee else ''
            record.last_name = record.employee.s_last_name if record.employee else ''
            record.company = record.employee.company_id.name or ''
            record.gender = record.employee.gender or ''

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
                
class MedicalType (models.Model):
    _name = 'medical.type'
    _description = 'Medical Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Medical Type', required=True)
    description = fields.Char(string='Description')

