# Part of Odoo. See LICENSE file for full copyright and licensing details.

from .common import TestPayslipBase


class TestPayslipFlow(TestPayslipBase):
    def setUp(self):
        super().setUp()

        # I create a base salary structure
        self.structure_base = self.PayrollStructure.create(
            {
                "name": "Base Salary Structure",
                "code": "BASE",
                "rule_ids": [
                    (4, self.rule_basic.id),
                    (4, self.rule_gross.id),
                    (4, self.rule_net.id),
                ],
            }
        )

        # I create a salary structure with Meal
        self.structure_meal = self.PayrollStructure.create(
            {
                "name": "Salary Structure with Meal",
                "code": "SP",
                "parent_id": self.structure_base.id,
                "company_id": self.ref("base.main_company"),
                "rule_ids": [
                    (4, self.rule_meal.id),
                ],
            }
        )

    def test_structure_get_all_rules(self):
        all_rules = self.structure_meal.get_all_rules()
        expected_rules = (
            self.rule_child
            | self.structure_base.rule_ids
            | self.structure_meal.rule_ids
        )
        self.assertEqual(
            all_rules,
            expected_rules,
            "The rules returned correspond to the rules in the salary structures",
        )
        self.assertEqual(
            len(all_rules),
            len(expected_rules),
            "There are no duplicates in returned rules",
        )
