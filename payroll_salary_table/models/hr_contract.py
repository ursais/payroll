# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import _, exceptions, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    def get_master_data_line(self, data_type):
        self.ensure_one()
        value_line = self.active_values_ids.filtered(
            lambda x: x.type_id == data_type or x.type_id.code == data_type
        )
        return value_line[:1]

    def get_master_data_value(self, data_type):
        return self.get_master_data_line(data_type).get_value()

    def _get_salary_table_domain(self, table_code, rule_code=None, amount=0):
        SalaryTableTemplate = self.env["hr.salary.table.template"]
        template = SalaryTableTemplate.search([("code", "=", table_code)])
        if not template:
            raise exceptions.UserError(
                _("Salary Table Template %s not found", table_code)
            )
        domain = [("template_id", "=", template.id)]
        if template.type_1_id:
            value_1 = self.get_master_data_value(template.type_1_id)
            domain.append(("type_1_id", "=", value_1))
        if template.type_2_id:
            value_2 = self.get_master_data_value(template.type_1_id)
            domain.append(("type_2_id", "=", value_2))
        if template.type_3_id:
            value_3 = self.get_master_data_value(template.type_1_id)
            domain.append(("type_3_id", "=", value_3))
        if template.has_lower_bound:
            domain.append(("number_from", ">=", amount))
        if template.has_upper_bound:
            domain.append(("number_to", "<=", amount))
        if rule_code:
            domain.append(("salary_rule_id.code", "=", rule_code))
        return domain

    def salary_table(self, table_code, rule_code=None, amount=0):
        domain = self._get_salary_table_domain(table_code, rule_code, amount)
        # TODO: optimize performance, avoiding reload per payslip
        lines = self.env["hr.salary.table.line"].search(domain)
        return lines[-1:].result
