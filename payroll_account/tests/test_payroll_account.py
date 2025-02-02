# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from dateutil import relativedelta

from odoo import fields
from odoo.tests import common


class TestPayrollAccount(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Activate company currency
        self.env.user.company_id.currency_id.active = True

        self.payslip_action_id = self.ref("payroll.hr_payslip_menu")

        self.res_partner_bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "001-9876543-21",
                "partner_id": self.ref("base.res_partner_12"),
                "acc_type": "bank",
                "bank_id": self.ref("base.res_bank_1"),
            }
        )

        self.hr_employee_john = self.env["hr.employee"].create(
            {
                "address_id": self.ref("base.res_partner_address_27"),
                "birthday": "1984-05-01",
                "children": 0.0,
                "country_id": self.ref("base.in"),
                "department_id": self.ref("hr.dep_rd"),
                "gender": "male",
                "marital": "single",
                "name": "John",
                "bank_account_id": self.res_partner_bank.bank_id.id,
            }
        )

        # Taxes
        AccountTag = self.env["account.account.tag"]
        AccountTax = self.env["account.tax"]
        # Income Tax
        self.income_tax = AccountTax.create(
            {"name": "Income Tax", "type_tax_use": "none"}
        )
        self.tax_tag_base = AccountTag.create(
            {"name": "A101-base", "applicability": "taxes"}
        )
        self.tax_tag_tax = AccountTag.create(
            {"name": "A201-tax", "applicability": "taxes"}
        )
        self.income_tax.invoice_repartition_line_ids[0].tag_ids = self.tax_tag_base
        self.income_tax.invoice_repartition_line_ids[1].tag_ids = self.tax_tag_tax
        # Social Security
        self.social_security = AccountTax.create(
            {"name": "Social Security", "type_tax_use": "none"}
        )
        self.ss_tag_base = AccountTag.create(
            {"name": "S101-base", "applicability": "taxes"}
        )
        self.ss_tag_tax = AccountTag.create(
            {"name": "S201-tax", "applicability": "taxes"}
        )
        self.social_security.invoice_repartition_line_ids[0].tag_ids = self.ss_tag_base
        self.social_security.invoice_repartition_line_ids[1].tag_ids = self.ss_tag_tax

        # Accounts Setup
        Account = self.env["account.account"]
        self.account_debit = Account.create(
            {"name": "Salaries", "code": "630", "account_type": "expense"}
        )
        self.account_credit = Account.create(
            {
                "name": "Salaries Payable",
                "code": "230",
                "account_type": "liability_current",
                "reconcile": True,
            }
        )
        self.account_tax = Account.create(
            {
                "name": "Tax Payable",
                "code": "231",
                "account_type": "liability_current",
                "reconcile": True,
            }
        )
        self.account_ss = Account.create(
            {
                "name": "SS Payable",
                "code": "232",
                "account_type": "liability_current",
                "reconcile": True,
            }
        )

        self.account_journal = self.env["account.journal"].create(
            {
                "name": "Vendor Bills - Test",
                "code": "TEXJ",
                "type": "purchase",
                "default_account_id": self.account_debit.id,
                "refund_sequence": True,
            }
        )

        rules = [
            self.ref("payroll.hr_salary_rule_houserentallowance1"),
            self.ref("payroll.hr_salary_rule_professionaltax1"),
            self.ref("payroll.hr_salary_rule_providentfund1"),
        ]
        self.hr_structure_softwaredeveloper = self.env["hr.payroll.structure"].create(
            {
                "name": "Salary Structure for Software Developer",
                "code": "SD",
                "parent_id": self.ref("payroll.structure_base"),
                "journal_id": self.account_journal.id,
                "rule_ids": [(6, 0, rules)],
            }
        )

        self.hr_contract_john = self.env["hr.contract"].create(
            {
                "date_end": fields.Date.to_string(datetime.now() + timedelta(days=365)),
                "date_start": fields.Date.today(),
                "name": "Contract for John",
                "wage": 5000.0,
                "employee_id": self.hr_employee_john.id,
                "struct_id": self.hr_structure_softwaredeveloper.id,
            }
        )

    def _update_account_in_rule(self):
        self.rule_basic = self.env.ref("payroll.hr_rule_basic")
        self.rule_basic.write({"account_debit": self.account_debit.id})

        self.hr_rule_net = self.env.ref("payroll.hr_rule_net")
        self.hr_rule_net.write({"account_credit": self.account_credit.id})

        self.rule_tax = self.env.ref("payroll.hr_salary_rule_professionaltax1")
        self.rule_tax.write(
            {
                "account_credit": self.account_tax.id,
                "account_tax_id": self.income_tax.id,
                "repartition_type": "tax",
            }
        )

        self.rule_social_security = self.env.ref(
            "payroll.hr_salary_rule_providentfund1"
        )
        self.rule_social_security.write(
            {
                "account_credit": self.account_ss.id,
                "account_tax_id": self.social_security.id,
                "repartition_type": "tax",
            }
        )

    def _prepare_payslip(self, employee):
        date_from = datetime.now()
        date_to = datetime.now() + relativedelta.relativedelta(
            months=+1, day=1, days=-1
        )
        self.hr_payslip = self.env["hr.payslip"].create(
            {
                "employee_id": self.hr_employee_john.id,
                "contract_id": self.hr_contract_john.id,
                "struct_id": self.hr_structure_softwaredeveloper.id,
            }
        )
        res = self.hr_payslip.get_payslip_vals(date_from, date_to, employee.id)
        vals = {
            "name": res["value"]["name"],
            "worked_days_line_ids": [
                (0, 0, i) for i in res["value"]["worked_days_line_ids"]
            ],
            "input_line_ids": [(0, 0, i) for i in res["value"]["input_line_ids"]],
        }
        self.hr_payslip.write(vals)
        return self.hr_payslip

    def test_00_hr_payslip(self):
        """checking the process of payslip."""
        self._update_account_in_rule()
        self._prepare_payslip(self.hr_employee_john)

        # I assign the amount to Input data.
        payslip_input = self.env["hr.payslip.input"].search(
            [("payslip_id", "=", self.hr_payslip.id)]
        )
        payslip_input.write({"amount": 5.0})

        # I verify the payslip is in draft state.
        self.assertEqual(self.hr_payslip.state, "draft", "State not changed!")

        # I click on "Compute Sheet" button.
        self.hr_payslip.with_context(
            {},
            lang="en_US",
            tz=False,
            active_model="hr.payslip",
            department_id=False,
            active_ids=[self.payslip_action_id],
            section_id=False,
            active_id=self.payslip_action_id,
        ).compute_sheet()

        # I want to check cancel button.
        # So I first cancel the sheet then make it set to draft.
        self.hr_payslip.action_payslip_cancel()
        self.assertEqual(self.hr_payslip.state, "cancel", "Payslip is rejected.")
        self.hr_payslip.action_payslip_draft()

        self.hr_payslip.action_payslip_done()

        # I verify that the Accounting Entries are created.
        self.assertTrue(self.hr_payslip.move_id, "Accounting Entries should be created")

        # I verify that the payslip is in done state.
        self.assertEqual(self.hr_payslip.state, "done", "State not changed!")

        # Check Tax line has Tax and Tags set
        lines = self.hr_payslip.move_id.line_ids
        tax_line = lines.filtered(lambda x: x.account_id == self.account_tax)
        ss_line = lines.filtered(lambda x: x.account_id == self.account_ss)
        self.assertEqual(
            tax_line.tax_tag_ids,
            self.tax_tag_tax,
            "Income Tax Journal Item should have Tax Tags",
        )
        self.assertEqual(
            ss_line.tax_tag_ids,
            self.ss_tag_tax,
            "Social Security Journal Item should have Tax Tags",
        )

    def test_hr_payslip_no_accounts(self):
        self._prepare_payslip(self.hr_employee_john)

        # I click on "Compute Sheet" button.
        self.hr_payslip.with_context(
            {},
            lang="en_US",
            tz=False,
            active_model="hr.payslip",
            department_id=False,
            active_ids=[self.payslip_action_id],
            section_id=False,
            active_id=self.payslip_action_id,
        ).compute_sheet()

        # Confirm Payslip (no account moves)
        self.hr_payslip.action_payslip_done()
        self.assertFalse(self.hr_payslip.move_id, "Accounting Entries has been created")

        # I verify that the payslip is in done state.
        self.assertEqual(self.hr_payslip.state, "done", "State not changed!")
