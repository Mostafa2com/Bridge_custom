from collections import defaultdict
from datetime import timedelta
from operator import itemgetter

from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby


class StockMove(models.Model):
    _inherit = "stock.move"

    product_uom_qty = fields.Float(
        'Demand',
        digits='Product Unit of Measure',
        default=1.0, required=True, states={'done': [('readonly', True)]},
        help="This is the quantity of products from an inventory "
             "point of view. For moves in the state 'done', this is the "
             "quantity of products that were actually moved. For other "
             "moves, this is the quantity of product that is planned to "
             "be moved. Lowering this quantity does not generate a "
             "backorder. Changing this quantity on assigned moves affects "
             "the product reservation, and should be done with care.")

    quantity_done = fields.Float(
        'Quantity Done')

    @api.constrains('quantity_done')
    def _check_quantity_done(self):
        for move in self:
            if move.product_uom_qty < move.quantity_done:
                raise UserError("Can't Exceed the quantity ordered")
