# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    # _name = 'account.setting'
    _inherit = 'res.config.settings'

    account_checker = fields.Boolean(string='Check Account Code')
    purchase_checker = fields.Boolean(string='Check Purchase Received Qty')
