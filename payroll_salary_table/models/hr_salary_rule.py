# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    def _compute_rule_code(self, localdict):
        # When calculating a Python code rule
        # the lookup_tables function is available for the rule code
        # to get the applicable value for a salary rule code.
        # Example:  result = lookup_tables("TAXRATE", taxable_amount)
        def lookup_tables(rule_code, amount=0):
            salary_table_lines = self.env.context.get("salary_table_lines")
            contract = localdict["contract"]
            return salary_table_lines.lookup_rule(contract, rule_code, amount)

        localdict["lookup_tables"] = lookup_tables
        return super()._compute_rule_code(localdict)

    def _get_rule_dict(self, localdict):
        # After calculating a salary rule,
        # the result_data variable ican be stored in the Payslip line.
        # This allows salary rules to calculate and stor a Master Data Value,
        # that can later be be useful for audit or reporting.
        res = super()._get_rule_dict(localdict)
        if "result_data" in localdict:
            res["data_value_id"] = float(localdict["result_data"])
        return res
