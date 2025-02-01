# Copyright 2025 Open Source Integrators
from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    journal_id = fields.Many2one(
        "account.journal",
        "Salary Journal",
        company_dependent=True,
    )
