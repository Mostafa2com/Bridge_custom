from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'





    def action_confirm(self):
        val = super().action_confirm()
        try:
            for order in self:
                for line in order.order_line:
                    line.lot_id.write({'reserved_by': order.user_id.name})
        except ValueError:
            pass
        return val

    def action_cancel(self):
        val = super().action_cancel()
        try:
            for order in self:
                for line in order.order_line:
                    line.lot_id.write({'reserved_by': ""})
        except ValueError:
            pass
        return val


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(string="Quantity", defualt=1, compute="_compute_qty", store=True)

    def _compute_qty(self):
        for line in self:
            line.product_uom_qty = 1

    @api.onchange('lot_id')
    def _onchange_lot_scan(self):
        lot_rec  = self.env['stock.lot']
        if self.lot_id:
            lotProduct = lot_rec.search([('id','=',self.lot_id.id)])
            self.product_id = lotProduct.product_id