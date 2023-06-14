from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def create(self, vals_list):
        val = super().create(vals_list)
        try:
            for line in val.invoice_line_ids:
                line.write({'lot_id': line.sale_line_ids.lot_id.name})
        except ValueError:
            pass
        return val


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    lot_id = fields.Char(string='Lot', readonly='True')
