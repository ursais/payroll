# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def compute_sheet(self):
        # Set active_date in the context
        # To be used to filter active Master Data Values
        if self and not self.env.context.get("active_date"):
            date_to = self[0].date_to
            self = self.with_context(active_date=date_to)
        return super().compute_sheet()
