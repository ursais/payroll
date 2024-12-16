# Copyright 2025 Open Source Integrators (www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class HrContract(models.Model):
    _inherit = "hr.contract"

    def action_open_master_data(self):
        self.ensure_one()
        xmlid = "hr_master_data.action_hr_employee_data_value"
        action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
        action.update(
            {
                "domain": [("contract_id", "=", self.id)],
                "context": {"default_contract_id": self.id},
            }
        )
        return action
