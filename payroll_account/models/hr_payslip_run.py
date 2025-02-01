# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    journal_id = fields.Many2one(
        "account.journal",
        "Salary Journal",
        related="struct_id.journal_id",
        required=True,
        readonly=False,
        store=True,
    )
