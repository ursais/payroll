# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.depends("payslip_run_id", "struct_id")
    def _compute_journal_id(self):
        for payslip in self:
            payslip.journal_id = (
                payslip.payslip_run_id.journal_id or payslip.struct_id.journal_id
            )

    journal_id = fields.Many2one(
        "account.journal",
        compute="_compute_journal_id",
        check_company=True,
        store=True,
        readonly=False,
    )
    date = fields.Date(
        "Date Account",
        help="Keep empty to use the period of the validation(Payslip) date.",
    )
    move_id = fields.Many2one(
        "account.move", "Accounting Entry", readonly=True, copy=False
    )

    def action_payslip_cancel(self):
        for payslip in self:
            if not payslip.move_id.journal_id.restrict_mode_hash_table:
                payslip.move_id.with_context(force_delete=True).button_cancel()
                payslip.move_id.with_context(force_delete=True).unlink()
            else:
                payslip.move_id._reverse_moves()
                payslip.move_id = False
        return super().action_payslip_cancel()

    def action_payslip_done(self):
        res = super().action_payslip_done()

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            currency = (
                slip.company_id.currency_id or slip.journal_id.company_id.currency_id
            )

            name = _("Payslip of %s") % (slip.employee_id.name)
            move_dict = {
                "narration": name,
                "ref": slip.number,
                "journal_id": slip.journal_id.id,
                "date": date,
            }
            for line in slip.line_ids:
                amount = currency.round(slip.credit_note and -line.total or line.total)
                if currency.is_zero(amount):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                move_line_analytic_ids = {}
                if slip.contract_id.analytic_account_id:
                    move_line_analytic_ids.update(
                        {line.slip_id.contract_id.analytic_account_id.id: 100}
                    )
                elif line.salary_rule_id.analytic_account_id:
                    move_line_analytic_ids.update(
                        {line.salary_rule_id.analytic_account_id.id: 100}
                    )

                if debit_account_id:
                    debit_line = self._prepare_debit_line(
                        line, amount, date, debit_account_id, move_line_analytic_ids
                    )
                    line_ids.append((0, 0, debit_line))
                    debit_sum += debit_line["debit"] - debit_line["credit"]

                if credit_account_id:
                    credit_line = self._prepare_credit_line(
                        line,
                        amount,
                        date,
                        credit_account_id,
                        move_line_analytic_ids,
                    )
                    line_ids.append((0, 0, credit_line))
                    credit_sum += credit_line["credit"] - credit_line["debit"]

            if currency.compare_amounts(credit_sum, debit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _(
                            'The Expense Journal "%s" has not properly '
                            "configured the Credit Account!"
                        )
                        % (slip.journal_id.name)
                    )
                adjust_credit = self._prepare_adjust_credit_line(
                    currency, credit_sum, debit_sum, slip.journal_id, date
                )
                line_ids.append([0, 0, adjust_credit])

            elif currency.compare_amounts(debit_sum, credit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _(
                            'The Expense Journal "%s" has not properly '
                            "configured the Debit Account!"
                        )
                        % (slip.journal_id.name)
                    )
                adjust_debit = self._prepare_adjust_debit_line(
                    currency, credit_sum, debit_sum, slip.journal_id, date
                )
                line_ids.append([0, 0, adjust_debit])

            if len(line_ids) > 0:
                move_dict["line_ids"] = line_ids
                move = self.env["account.move"].create(move_dict)
                slip.write({"move_id": move.id, "date": date})
                move.action_post()
            else:
                logger.info(
                    f"Payslip {slip.number} did not generate any account move lines"
                )
        return res

    def _prepare_debit_line(
        self, line, amount, date, debit_account_id, move_line_analytic_ids
    ):
        tax_ids, tax_tag_ids, tax_repartition_line_id = self._get_tax_details(line)
        return {
            "name": line.name,
            "partner_id": line._get_partner_id(credit_account=False),
            "account_id": debit_account_id,
            "journal_id": line.slip_id.journal_id.id,
            "date": date,
            "debit": amount > 0.0 and amount or 0.0,
            "credit": amount < 0.0 and -amount or 0.0,
            "analytic_distribution": move_line_analytic_ids,
            "tax_line_id": line.salary_rule_id.account_tax_id.id,
            "tax_ids": tax_ids,
            "tax_repartition_line_id": tax_repartition_line_id,
            "tax_tag_ids": tax_tag_ids,
        }

    def _prepare_credit_line(
        self, line, amount, date, credit_account_id, move_line_analytic_ids
    ):
        tax_ids, tax_tag_ids, tax_repartition_line_id = self._get_tax_details(line)
        return {
            "name": line.name,
            "partner_id": line._get_partner_id(credit_account=True),
            "account_id": credit_account_id,
            "journal_id": line.slip_id.journal_id.id,
            "date": date,
            "debit": amount < 0.0 and -amount or 0.0,
            "credit": amount > 0.0 and amount or 0.0,
            "analytic_distribution": move_line_analytic_ids,
            "tax_line_id": line.salary_rule_id.account_tax_id.id,
            "tax_ids": tax_ids,
            "tax_repartition_line_id": tax_repartition_line_id,
            "tax_tag_ids": tax_tag_ids,
        }

    def _prepare_adjust_credit_line(
        self, currency, credit_sum, debit_sum, journal, date
    ):
        acc_id = journal.default_account_id.id
        return {
            "name": _("Adjustment Entry"),
            "partner_id": False,
            "account_id": acc_id,
            "journal_id": journal.id,
            "date": date,
            "debit": 0.0,
            "credit": currency.round(debit_sum - credit_sum),
        }

    def _prepare_adjust_debit_line(
        self, currency, credit_sum, debit_sum, journal, date
    ):
        acc_id = journal.default_account_id.id
        return {
            "name": _("Adjustment Entry"),
            "partner_id": False,
            "account_id": acc_id,
            "journal_id": journal.id,
            "date": date,
            "debit": currency.round(credit_sum - debit_sum),
            "credit": 0.0,
        }

    def _get_tax_details(self, line):
        tax = line.salary_rule_id.account_tax_id
        tax_ids = [(4, tax.id, 0)]

        tax_repart_lines = tax.invoice_repartition_line_ids
        tags = tax_repart_lines.tag_ids
        tax_tag_ids = [(4, tag.id, 0) for tag in tags]

        return tax_ids, tax_tag_ids, None
