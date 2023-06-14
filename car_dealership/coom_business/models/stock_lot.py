from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    reserved_by = fields.Char(string='Reserved By', readonly=True)
