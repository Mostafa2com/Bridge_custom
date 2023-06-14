from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from bisect import bisect_left
from collections import defaultdict
import re


class StockLot(models.Model):
    _inherit = 'stock.lot'

    reserved_by = fields.Char(string='Reserved By', readonly=True)


    # @api.onchange('orders')
    # def check_order(self, orders):
    #     self.create_uid = orders.order_id.user_id
