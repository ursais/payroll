# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrPayrollStructure(models.Model):
    """
    Salary structure used to defined
    - Basic
    - Allowances
    - Deductions
    """

    _name = "hr.payroll.structure"
    _description = "Salary Structure"

    @api.model
    def _get_parent(self):
        return self.env.ref("hr_payroll.structure_base", False)

    name = fields.Char(required=True)
    code = fields.Char(string="Reference")
    company_id = fields.Many2one("res.company")
    note = fields.Text(string="Description")
    parent_id = fields.Many2one(
        "hr.payroll.structure", string="Parent", default=_get_parent
    )
    children_ids = fields.One2many(
        "hr.payroll.structure", "parent_id", string="Children", copy=True
    )
    rule_ids = fields.Many2many(
        "hr.salary.rule",
        "hr_structure_salary_rule_rel",
        "struct_id",
        "rule_id",
        string="Salary Rules",
    )
    require_code = fields.Boolean(
        "Require code",
        compute="_compute_require_code",
        default=lambda self: self._compute_require_code(),
    )

    def _compute_require_code(self):
        require = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("payroll.require_code_and_category")
        )
        self.require_code = require
        return require

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(_("You cannot create a recursive salary structure."))

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, code=_("%s (copy)") % self.code)
        return super().copy(default)

    def _get_parent_structure(self):
        """
        Returns recordset of salary structures and their parents,
        ordered by hierarchy, parents first
        """
        if not self:
            return self.env["hr.payroll.structure"]
        else:
            return self.parent_id._get_parent_structure() | self

    def get_all_rules(self):
        """
        Returns a recordset of all rules for the struture and parents,
        in proper calculation order:

        1. By sequence of parent Rules, regardless of the Structure they belong to.
           The Structure parent/child levels are not relevant.
        2. For each rule, the child rules preceed the parent rule.

        @return: ordered recordset of Salary Rule
        """
        structures = self._get_parent_structure()
        sorted_rules = self.env["hr.salary.rule"]
        for rule in structures.rule_ids:
            sorted_rules |= rule._recursive_search_of_rules()
        return sorted_rules
