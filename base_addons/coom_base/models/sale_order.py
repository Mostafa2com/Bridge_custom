from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order.line'






