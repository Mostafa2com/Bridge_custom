from odoo import fields, models, api
from odoo.exceptions import ValidationError


def _set_user_groups(user_id, job_id):
    if user_id:
        if job_id.job_groups:
            user_id.groups_id = [(6, 0, job_id.job_groups.ids)]
        else:
            raise ValidationError("The Selected Job Position is Not Liked to Any Security Group: ")
    else:
        raise ValidationError("Link Employee to User: Contact Your Administrator")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        result = super(HrEmployee, self).create(vals)
        _set_user_groups(result.user_id, result.job_id)
        return result

    # def create(self, vals_list):
    #     val = super().create(vals_list)
    #     try:
    #         _set_user_groups(val.user_id, val.job_id)
    #     except ValueError:
    #         pass
    #     return val

    @api.onchange('job_id', 'user_id')
    def _get_job_groups(self):
        if self.id.origin:
            print(self.id)
            for record in self:
                _set_user_groups(record.user_id, record.job_id)
    pass

    pass
