# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    sponsor_id = fields.Many2one('res.partner')
    campo_vacio = fields.Boolean('Campo vacio', default=False)  
    
    payulatam_order_id = fields.Char('ID de Orden de PayU')
    payulatam_transaction_id = fields.Char('ID de Transacción de PayU')
    payulatam_signature = fields.Char('Signature de la Transacción')
    payulatam_state = fields.Char('Estado Transacción de PayU')
    payulatam_datetime = fields.Datetime('Fecha y Hora de la Transacción')
    payulatam_credit_card_token = fields.Char('Token Para Tarjetas de Crédito')
    payulatam_credit_card_masked = fields.Char('Mascara del Número de Tarjeta')
    payulatam_credit_card_identification = fields.Char('Identificación')
    payulatam_credit_card_method = fields.Char('Metodo de Pago')
    payulatam_request_expired = fields.Boolean('Request Expired')
    state =  fields.Selection(selection_add=[('finalized', 'Finalizado')], selection_remove=['payu_pending','payu_approved'])
#     main_product_id = fields.Many2one('product.product', string="Plan Elegido", compute="_compute_main_product_id", store=True)
    payment_method_type = fields.Selection([
        ("Credit Card", "Tarjeta de Crédito"), 
        ("Cash", "Efectivo"), 
        ("PSE", "PSE"),
        ("Product Without Price", "Producto con Precio $0"),
    ])
    
    
    def post(self):
        res = super(AccountMove, self).post()
        if self.sponsor_id:
            if not self.sponsor_id.generates_accounting:
                self.write({
                    'state': 'finalized'
                })
        return res
    
    
    def _cron_payment_invoice(self):
        invoices_ids = self.env['account.move'].search([('amount_residual', '>', 0), ('type', '=', 'out_invoice'), ('state', '=', 'posted'), ('journal_id', '=', 15)])
        for invoice in invoices_ids:
            Payment = self.env['account.payment'].with_context(active_ids=invoice.ids, active_model='account.move', active_id=invoice.id)
            payments_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'company_id': 1,
                'amount': invoice.amount_residual,
                'payment_date': fields.Datetime.now(),
                'journal_id': 9,
                'payment_method_id': 1
            }
            payments = Payment.create(payments_vals)
            payments.post()