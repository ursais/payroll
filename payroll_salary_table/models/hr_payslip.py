# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_all_salary_table_lines(self):
        """
        Return the active Salary Table lines, to be fetched and stored once,
        and then be available for queries by salary rules.
        """
        active_date = self[0].date_to
        salary_structures = self.contract_id.struct_id
        rules = salary_structures.get_all_rules()
        return rules.get_all_salary_table_lines(active_date)

    def _get_global_data(self):
        """
        Cached data, computed once an then shared by all the payslip calculations.
        To be used in Salary Rules code calculations (_compute_rule_code)
        """
        return {"salary_table_lines": self._get_all_salary_table_lines()}

    def compute_sheet(self):
        # Set active_date in the context
        # To be used to filter active Master Data Values
        global_data = self._get_globaldict()
        active_date = self[0].date_to
        self = self.with_context(active_date=active_date, global_data=global_data)
        return super().compute_sheet()
