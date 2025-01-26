# Copyright 2015 Savoir-faire Linux. All Rights Reserved.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    hr_period_id = fields.Many2one("hr.period", string="Period")
    date_payment = fields.Date(
        "Date of Payment",
        related="payslip_run_id.date_payment",
        store=True,
        readonly=False,
    )
    date_from = fields.Date(
        related="payslip_run_id.date_start", store=True, readonly=False
    )
    date_to = fields.Date(related="payslip_run_id.date_end", store=True, readonly=False)

    @api.constrains("hr_period_id", "company_id")
    def _check_period_company(self):
        for slip in self:
            if slip.hr_period_id and slip.hr_period_id.company_id != slip.company_id:
                if slip.hr_period_id.company_id != slip.company_id:
                    raise UserError(
                        _(
                            "The company on the selected period must be the same "
                            "as the company on the payslip."
                        )
                    )

    @api.onchange("company_id", "contract_id")
    def onchange_company_id(self):
        if self.company_id:
            if self.contract_id:
                contract = self.contract_id
                period = self.env["hr.period"].get_next_period(
                    self.company_id.id, contract.schedule_pay
                )
            else:
                schedule_pay = self.env["hr.payslip.run"].get_default_schedule(
                    self.company_id.id
                )
                if self.company_id and schedule_pay:
                    period = self.env["hr.period"].get_next_period(
                        self.company_id.id, schedule_pay
                    )
            self.hr_period_id = period.id if period else False

    @api.onchange("contract_id")
    def onchange_contract_period(self):
        if self.contract_id.employee_id and self.contract_id:
            employee = self.contract_id.employee_id
            contract = self.contract_id
            period = self.env["hr.period"].get_next_period(
                employee.company_id.id, contract.schedule_pay
            )
            if period:
                self.hr_period_id = period.id if period else False
