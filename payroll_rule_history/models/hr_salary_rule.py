# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")

    # TODO: remove from "payroll" as not used anymore
    # def _recursive_search_of_rules(self):

    def _get_all_rules_and_childs(self):
        """
        Lists all rules and their childs at a provided date.
        Used by the Payslip computation to find the applicable rules.
        """
        rules = self
        active_date = self.env.context.get("active_date")
        if active_date:
            rules = rules.filtered(
                lambda x: (not x.date_start or x.date_start <= active_date)
                and (not x.date_end or active_date <= x.date_end)
            )
        if rules.child_ids:
            rules |= self.child_ids._get_all_rules_and_childs()
        return rules
