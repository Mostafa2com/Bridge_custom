from odoo import fields, models, api


class HrJob(models.Model):
    _inherit = 'hr.job'

    job_groups = fields.Many2many('res.groups', string="Security Groups")

    @api.onchange('job_groups')
    def _update_employee_user_groups(self):
        for record in self:
            current_groups = record.job_groups
            employees_in_job = self.env['hr.employee'].search([('job_id', '=', record.id.origin),
                                                               ('user_id', '!=', 'False')])
            if employees_in_job:
                for employee in employees_in_job:
                    employee.user_id.groups_id = [(6, 0, current_groups.ids)]
            record.job_groups = current_groups

    @api.model
    def _update_user_groups(self):
        for record in self.env['hr.job'].search([]):
            current_groups = record.job_groups
            employees_in_job = self.env['hr.employee'].search([('job_id', '=', record.id),
                                                               ('user_id', '!=', 'False')])
            if employees_in_job:
                for employee in employees_in_job:
                    employee.user_id.groups_id = [(6, 0, current_groups.ids)]

        return

