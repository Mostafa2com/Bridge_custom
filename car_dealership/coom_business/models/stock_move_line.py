from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'stock.move.line'


    @api.onchange('lot_id')
    def _onchange_lot_scan(self):
        lot_rec  = self.env['stock.lot']
        # product_rec = self.env['product.product']

        if self.lot_id:
            lotid = self.lot_id.id
            lotProduct = lot_rec.search([('id','=',lotid)])
            self.product_id = lotProduct.product_id