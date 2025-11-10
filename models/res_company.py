# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    tax_per_sircar_misiones = fields.Many2one(
        'account.tax',
        'Impuesto de Percepción Misiones',
        domain=[('type_tax_use', '=', 'sale'),('tax_group_id.l10n_ar_tribute_afip_code','=','07')], 
        company_dependent=True
    )

    regimen_misiones_ret = fields.Many2one(
        'sircar.regimenes','Regimen Retenciones Misiones', domain=[('n_jur', '=', '914'),('id_tipo','=','R')], 
        company_dependent=True
    )
    regimen_misiones_per = fields.Many2one(
        'sircar.regimenes','Regimen Percepciones Misiones', domain=[('n_jur', '=', '914'),('id_tipo','=','P')], 
        company_dependent=True 
    )