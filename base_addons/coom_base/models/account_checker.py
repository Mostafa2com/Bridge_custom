from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re



ACCOUNT_CODE_REGEX = re.compile(r'^[0-9]{0,14}$')
class AccountAccount(models.Model):

    _inherit = 'account.account'

    code = fields.Char(size=64, required=True, tracking=True)
    deprecated = fields.Boolean(default=False, tracking=True)



    account_type = fields.Selection(
        selection=[
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("expense", "Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),
            ("off_balance", "Off-Balance Sheet"),
        ],
        string="Type", tracking=True,
        required=True,
        store=True, readonly=False,
        # help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries."
    )

    @api.constrains('code')
    def _check_account_code(self):
        for account in self:
            if not re.match(ACCOUNT_CODE_REGEX, account.code):
                raise ValidationError(_(
                    "The account code can only numbers with 14 digits maximum."
                ))
    @api.constrains('code')
    def _check_deprecation(self):
        for record in self:
            if (len(record.code) != 7):
                record.deprecated = True

    @api.constrains('account_type')
    def _check_code(self):
        for record in self:
            if (record.code[0] != '1' and record.account_type in 'asset_receivable') \
                    or (record.code[0] != '1' and record.account_type in 'asset_current') or (
                    record.code[0] != '1' and record.account_type in 'asset_cash') \
                    or (record.code[0] != '1' and record.account_type in 'asset_non_current') or (
                    record.code[0] != '1' and record.account_type in 'asset_fixed') \
                    or (record.code[0] != '1' and record.account_type in 'asset_prepayments'):
                raise ValidationError('Assets Account Must begin with "1" ')
            elif (record.code[0] != '2' and record.account_type in 'liability_current') \
                    or (record.code[0] != '2' and record.account_type in 'Non-current Liabilities') \
                    or (record.code[0] != '2' and record.account_type in 'Payable') \
                    or (record.code[0] != '2' and record.account_type in 'liability_credit_card'):
                raise ValidationError('Liabilities Account Must begin with "2" ')
            elif (record.code[0] != '3' and record.account_type in 'equity') \
                    or (record.code[0] != '3' and record.account_type in 'equity_unaffected'):
                raise ValidationError('Equity Account Must begin with "3" ')
            elif (record.code[0] != '4' and record.code[0] != '9' and record.account_type in 'income') \
                    or (record.code[0] != '4' and record.code[0] != '9' and record.account_type in 'income_other'):
                raise ValidationError('Income Account Must begin with "4" ')

            elif (record.code[0] != '5' and record.code[0] != '6' and record.code[
                0] != '7' and record.account_type in 'expense_direct_cost'):
                raise ValidationError('Cost of Revenue Account must begin with "5", "6", or "7"')

            elif (record.code[0] != '7' and record.account_type in 'expense'):
                raise ValidationError('Expenses Account Must begin with "7"') 
            elif (record.code[0] != '8' and record.account_type in 'expense_depreciation'):
                raise ValidationError('Depreciation Account Must begin with "8"')

