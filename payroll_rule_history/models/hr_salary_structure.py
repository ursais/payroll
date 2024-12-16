# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    # TODO: Overrides the payroll module method! Submit change there.
    # Also make HrSalaryRule._recursive_search_of_rules() redundant
    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe
                 to apply
        """
        # all_rules = []
        # for struct in self:
        #     all_rules += struct.rule_ids._recursive_search_of_rules()
        # return all_rules
        rules = self.rule_ids._get_all_rules_and_childs()
        return [(x.id, x.sequence) for x in rules]
