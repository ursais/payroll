from odoo import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    salary_table_lines_ids = fields.One2many(
        comodel_name="hr.salary.table.line",
        inverse_name="salary_rule_id",
    )
    active_salary_table_lines_ids = fields.One2many(
        comodel_name="hr.salary.table.line",
        compute="_compute_active_salary_table_lines_ids",
    )

    @api.depends_context("active_date")
    @api.depends("salary_table_lines_ids")
    def _compute_active_salary_table_lines_ids(self):
        """
        Lists only active salary table lines at a provided date.
        Used by the Payslip computation to query the salary table.
        """
        active_date = self.env.context.get("active_date")
        for rule in self:
            lines = rule.salary_table_lines_ids.filtered(
                lambda x: not active_date
                or (
                    (not x.date_start or x.date_start <= active_date)
                    and (not x.date_end or x.date_end >= active_date)
                )
            )
            rule.active_salary_table_lines_ids = lines
