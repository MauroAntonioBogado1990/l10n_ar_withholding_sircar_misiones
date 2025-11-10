# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    alicuota_per_misiones = fields.Float('Ali. Percepciones Misiones')
    alicuota_per_misiones_3 = fields.Boolean('Ali. Percepciones Misiones 3.31')
    alicuota_per_misiones_1 = fields.Boolean('Ali. Percepciones Misiones 1.96')
    alicuota_ret_misiones = fields.Float('Ali. Retenciones Misiones')
    alicuota_ret_misiones_3 = fields.Boolean('Ali. Retenciones Misiones 3.31')
    alicuota_ret_misiones_1 = fields.Boolean('Ali. Retenciones Misiones 1.96')

    def get_amount_alicuot_misiones(self,type_alicuot,date):
        amount_alicuot = 0.00
        if type_alicuot == 'per':
            if self.alicuota_per_misiones_3:
                amount_alicuot = 3.31
            elif self.alicuota_per_misiones_1:
                amount_alicuot = 1.96
            else:
                amount_alicuot = self.alicuota_per_misiones
        if type_alicuot == 'ret':
            if self.alicuota_ret_misiones_3:
                amount_alicuot = 3.31
            elif self.alicuota_ret_misiones_1:
                amount_alicuot = 1.96
            else:
                amount_alicuot = self.alicuota_ret_misiones
        return amount_alicuot
