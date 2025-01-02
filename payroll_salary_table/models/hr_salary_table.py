from odoo import api, fields, models


class HrSalaryTableTemplate(models.Model):
    _name = "hr.salary.table.template"
    _description = "Salary Table Template"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    type_1_id = fields.Many2one("hr.data.type")
    type_2_id = fields.Many2one("hr.data.type")
    type_3_id = fields.Many2one("hr.data.type")
    has_lower_bound = fields.Boolean()
    has_upper_bound = fields.Boolean()
    line_ids = fields.One2many(
        comodel_name="hr.salary.table",
        inverse_name="template_id",
    )
    note = fields.Text()
    active = fields.Boolean(default=True)


class HrSalaryTable(models.Model):
    _name = "hr.salary.table"
    _description = "Salary Table"

    template_id = fields.Many2one("hr.salary.table.template", required=True)
    company_id = fields.Many2one("res.company")
    date_start = fields.Date()
    date_end = fields.Date()
    line_ids = fields.One2many(
        comodel_name="hr.salary.table.line",
        inverse_name="table_id",
    )
    note = fields.Text()

    template_code = fields.Char(related="template_id.code")
    type_1_id = fields.Many2one("hr.data.type", related="template_id.type_1_id")
    type_2_id = fields.Many2one("hr.data.type", related="template_id.type_2_id")
    type_3_id = fields.Many2one("hr.data.type", related="template_id.type_3_id")
    has_lower_bound = fields.Boolean(related="template_id.has_lower_bound")
    has_upper_bound = fields.Boolean(related="template_id.has_upper_bound")


class HrSalaryTableLine(models.Model):
    _name = "hr.salary.table.line"
    _description = "Salary Table Line"
    _order = "table_id desc, value_1_id, value_2_id, value_3_id, number_from, number_to"

    table_id = fields.Many2one("hr.salary.table")
    salary_rule_id = fields.Many2one("hr.salary.rule")
    value_1_id = fields.Many2one(
        "hr.data.type.value",
        domain="[('type_id', '=', type_1_id)]",
    )
    value_2_id = fields.Many2one(
        "hr.data.type.value",
        domain="[('type_id', '=', type_2_id)]",
    )
    value_3_id = fields.Many2one(
        "hr.data.type.value",
        domain="[('type_id', '=', type_3_id)]",
    )
    number_from = fields.Float()
    number_to = fields.Float()
    result = fields.Float()

    template_id = fields.Many2one(
        "hr.salary.table.template", related="table_id.template_id", store=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company", related="table_id.company_id", store=True
    )
    date_start = fields.Date(related="table_id.date_start", store=True)
    date_end = fields.Date(related="table_id.date_end", store=True)

    template_code = fields.Char(related="table_id.template_id.code")
    type_1_id = fields.Many2one(
        "hr.data.type", related="table_id.template_id.type_1_id"
    )
    type_2_id = fields.Many2one(
        "hr.data.type", related="table_id.template_id.type_2_id"
    )
    type_3_id = fields.Many2one(
        "hr.data.type", related="table_id.template_id.type_3_id"
    )
    has_lower_bound = fields.Boolean(related="table_id.template_id.has_lower_bound")
    has_upper_bound = fields.Boolean(related="table_id.template_id.has_upper_bound")

    @api.model
    def _get_salary_table_domain(self, code, contract):
        template = self.env["hr.salary.table.template"].search([("code", "=", code)])
        domain = [("template_id", "=", template.id)]
        if template.type_1_id:
            domain.append(("type_1_id", "=", template.type_1_id.id))
        if template.type_2_id:
            domain.append(("type_2_id", "=", template.type_2_id.id))
        if template.type_3_id:
            domain.append(("type_3_id", "=", template.type_3_id.id))
        return domain
