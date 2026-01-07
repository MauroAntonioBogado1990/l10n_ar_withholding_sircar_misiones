# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,timedelta
from dateutil import relativedelta
import base64
import logging
import json
_logger = logging.getLogger(__name__)
try:
    from base64 import encodebytes
except ImportError:  # 3+
    from base64 import encodestring as encodebytes

class AccountExportSircarMisiones(models.Model):
    _name = 'account.export.sircar.misiones'
    _description = 'account.export.sircar.misiones'

    name = fields.Char('Nombre')
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    export_sircar_misiones_data_ret = fields.Text('Contenidos archivo SIRCAR Misiones Ret', default='')
    export_sircar_misiones_data_per = fields.Text('Contenidos archivo SIRCAR Misiones Per', default='')
    tax_withholding = fields.Many2one('account.tax','Imp. de ret utilizado', domain=[('tax_sircar_misiones_ret', '=', True)], required=True)
    
    #Retenciones
    @api.depends('export_sircar_misiones_data_ret')
    def _compute_files_ret(self):
        self.ensure_one()
        self.export_sircar_misiones_filename_ret = _('Sircar_misiones_ret_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_sircar_misiones_file_ret = encodebytes(self.export_sircar_misiones_data_ret.encode('ISO-8859-1'))
    export_sircar_misiones_file_ret = fields.Binary('TXT SIRCAR Misiones Ret',compute=_compute_files_ret)
    export_sircar_misiones_filename_ret = fields.Char('TXT SIRCAR Misiones Ret',compute=_compute_files_ret) 
    
    #Percepciones
    @api.depends('export_sircar_misiones_data_per')
    def _compute_files_per(self):
        self.ensure_one()
        self.export_sircar_misiones_filename_per = _('Sircar_misiones_per_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_sircar_misiones_file_per = encodebytes(self.export_sircar_misiones_data_per.encode('ISO-8859-1'))
    export_sircar_misiones_file_per = fields.Binary('TXT SIRCAR Misiones Per',compute=_compute_files_per)
    export_sircar_misiones_filename_per = fields.Char('TXT SIRCAR Misiones Per',compute=_compute_files_per)


    def compute_sircar_misiones_data(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        # Retenciones
        payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','not in',['cancel','draft']),('date','<=',self.date_to),('date','>=',self.date_from)])
        string = ''
        num_renglon = 1
        for payment in payments:
            if not payment.withholding_number:
                continue
            if payment.tax_withholding_id.id != self.tax_withholding.id:
                continue
            # TXT segun formato de https://www.comarb.gob.ar/descargar/sircar/Anexo_Registros.pdf
            if len(payment.partner_id) < 1:
                raise ValidationError('El pago {0} no tiene asignado un cliente'.format(payment.name))
            _alicuota_ret = payment.partner_id.get_amount_alicuot_misiones('ret',self.date_from)

            # 1 campo Fecha de Retención . Long: 10. Formato dd/mm/aaaa.
            string = string + str(payment.date)[8:10] + '-' + str(payment.date)[5:7] + '-' + str(payment.date)[:4] + ','
            # # 2 campo Tipo de Comprobante. Long: 1. 1 Comprobante de Retención / 2 Comprobante de Anulación de Retención
            string = string + 'CR' + ','
            # # 3 campo Número de Comprobante. Long: 12.
            string = string + payment.withholding_number.zfill(12) + ','
            # # 4 Razón social
            string = string + payment.partner_id.name + ','
            # 5 CUIT Contribuyente involucrado en la transacción Comercial . Long: 1. Ej: 30100100106
            string = string + str(payment.partner_id.vat) + ','
            # # 6 campo Monto Sujeto a Retención (numérico sin separador de miles)
            string = string + ("%.2f"%(payment.withholding_base_amount)) + ','
            # # 7 campo Alícuota (porcentaje sin separador de miles) . Ej: 42.03
            string = string + "%.2f"%_alicuota_ret
            # if payment.move_id.reversed_entry_id:
            #     # # 8 campo Tipo de Comprobante. Long: 1. 1 Comprobante de Retención / 2 Comprobante de Anulación de Retención [CAR]
            #     string = string + 'CR' + ','
            #     # # 9 campo Número de Comprobante. Long: 12. [CAR]
            #     string = string + str(payment.move_id.reversed_entry_id.payment_id.withholding_number.zfill(12)) + ','
            #     # 10 campo Fecha de Retención . Long: 10. Formato dd/mm/aaaa. [CAR]
            #     string = string + str(payment.move_id.reversed_entry_id.payment_id.date)[8:10] + '/' + str(payment.move_id.reversed_entry_id.payment_id.date)[5:7] + '/' + str(payment.move_id.reversed_entry_id.payment_id.date)[:4] + ','
            #     # 11 CUIT Contribuyente involucrado en la transacción Comercial . Long: 1. Ej: 30100100106 [CAR]
            #     string = string + str(payment.move_id.reversed_entry_id.payment_id.partner_id.vat) + ','
            # else:
            string = string + ',,,,'

            # CRLF
            string = string + windows_line_ending
            num_renglon += 1
            
        self.export_sircar_misiones_data_ret = string

        # Percepciones
        invoices = self.env['account.move'].search([('move_type','in',['out_invoice','out_refund']),('state','=','posted'),('invoice_date','<=',self.date_to),('invoice_date','>=',self.date_from)],order='invoice_date asc')
        string = ''
        string_txt = ''
        num_renglon = 1
        for invoice in invoices:
            #taxes = invoice.tax_totals['groups_by_subtotal']['Base imponible']
            groups = invoice.tax_totals.get('groups_by_subtotal', {})
            taxes = groups.get('Importe libre de impuestos') or groups.get('Base imponible') or []
                                             
            for tax in taxes:
                if tax['tax_group_name'] == 'Perc IIBB Misiones':
                    if invoice.currency_id.name != 'ARS':
                        for ml in invoice.line_ids:
                            if ml.name == 'Percepción IIBB Misiones Aplicada':
                                if invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                                    tax_group_amount = ml.debit
                                else:
                                    tax_group_amount = ml.credit
                    else:
                        tax_group_amount = tax['tax_group_amount']

                    # 1 Fecha de Percepción. Long: 10. (en formato dd/mm/aaaa) ej: 03/12/2015
                    string_txt = string_txt + str(invoice.invoice_date)[8:10] + '/' + str(invoice.invoice_date)[5:7] + '/' + str(invoice.invoice_date)[:4] + ','
                    # 2 Tipo de Comprobante original: 
                    if invoice.l10n_latam_document_type_id:
                        document_type_prefix = invoice.l10n_latam_document_type_id.doc_code_prefix
                        document_type_prefix = document_type_prefix.replace('-', '_')
                        string_txt = string_txt + str(document_type_prefix) + ','
                    else:
                        raise ValidationError('El tipo de documento de la factura {0} no tiene un prefijo asociado para mostrar en el txt.'.format(invoice.name))
                    # 3 Número de Comprobante (incluye el punto de venta) . Long: 12. Ej: 000023431222
                    string_txt = string_txt + str(invoice.name)[-13:-9] + str(invoice.name)[-8:] + ','
                    # 4 campo razon social Contribuyente involucrado en la transacción Comercial.
                    string_txt = string_txt + invoice.partner_id.name + ','
                    # 5 campo CUIT Contribuyente involucrado en la transacción Comercial. Long: . Formato 99-99999999-9
                    cuit = invoice.partner_id.vat
                    formatted_cuit = '{}-{}-{}'.format(cuit[:2], cuit[2:10], cuit[10:])
                    string_txt += formatted_cuit
                    # 6 Monto Sujeto a Percepción (numérico sin separador de miles). Ej: 999999999.99
                    if invoice.currency_id.name != 'ARS':
                        if invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                            string_txt = string_txt + "%.2f"%(tax['tax_group_base_amount'] * invoice.l10n_ar_currency_rate) + ','
                        else:
                            string_txt = string_txt + "%.2f"%(tax['tax_group_base_amount'] * invoice.l10n_ar_currency_rate) + ','
                    else:
                        if invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                            string_txt = string_txt + "%.2f"%tax['tax_group_base_amount'] + ','
                        else:
                            string_txt = string_txt + "%.2f"%tax['tax_group_base_amount'] + ','
                    # 7 campo Alícuota (porcentaje sin separador de miles) . Ej: 42.03
                    _alicuota_per = invoice.partner_id.get_amount_alicuot_misiones('per',self.date_from)
                    string_txt = string_txt + "%.2f"%_alicuota_per
                    
                    # Cuando es NC
                    # Campos obligatorios para la Nota de Crédito
                    if invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                        if not invoice.reversed_entry_id:
                            raise ValidationError('La factura {0} es una nota de crédito y no tiene una factura de reversion asociada'.format(invoice.name))
                        else:
                            # 8 Tipo de Comprobante original: 
                            if invoice.reversed_entry_id.l10n_latam_document_type_id:
                                document_type_prefix = invoice.reversed_entry_id.l10n_latam_document_type_id.doc_code_prefix
                                document_type_prefix = document_type_prefix.replace('-', '_')
                                string_txt = string_txt + str(document_type_prefix) + ','
                            else:
                                raise ValidationError('El tipo de documento de la factura {0} no tiene un prefijo asociado para mostrar en el txt.'.format(invoice.name))

                            # 9 Número de Comprobante original (incluye el punto de venta) . Long: 12. Ej: 000023431222
                            string_txt = string_txt + str(invoice.reversed_entry_id.name)[-13:-9] + str(invoice.reversed_entry_id.name)[-8:] + ','
                            # 10 Fecha de Comprobante original. Long: 10. (en formato dd/mm/aaaa) ej: 03/12/2015
                            string_txt = string_txt + str(invoice.reversed_entry_id.invoice_date)[8:10] + '/' + str(invoice.reversed_entry_id.invoice_date)[5:7] + '/' + str(invoice.reversed_entry_id.invoice_date)[:4] + ','
                            # 5 campo CUIT Contribuyente involucrado en la transacción Comercial. Long: . Formato 99-99999999-9
                            cuit = invoice.reversed_entry_id.partner_id.vat
                            formatted_cuit = '{}-{}-{}'.format(cuit[:2], cuit[2:10], cuit[10:])
                            string_txt += formatted_cuit
                    else:
                        string_txt = string_txt + ',,,,'

                    string_txt = string_txt + windows_line_ending

                    
        self.export_sircar_misiones_data_per = string_txt


