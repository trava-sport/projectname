# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class SaleCommission_1(models.Model):
    _name = "sale.commission_1"
    _description = "Комиссия в продажах"

    name = fields.Char("Название", required=True)
    commission_type = fields.Selection(
        selection=[("fixed", "Фиксированный процент"), ("section", "Процент зависящий от цены")],
        string="Тип комиссии",
        required=True,
        default="fixed",
    )
    fix_qty = fields.Float(string="Фиксированный процент")
    section_ids = fields.One2many(
        string="Разделы",
        comodel_name="sale.commission.section",
        inverse_name="commission_id",
    )
    active = fields.Boolean(string="Активный", default=True)
    invoice_state = fields.Selection(
        [("open", "Счет"), ("paid", "Оплата на основе")],
        string="Статус счета",
        required=True,
        default="open",
    )
    amount_base_type = fields.Selection(
        selection=[("gross_amount", "Ощая сумма"), ("net_amount", "Чистый доход")],
        string="Основа",
        required=True,
        default="gross_amount",
    )

    def calculate_section(self, base):
        self.ensure_one()
        for section in self.section_ids:
            if section.amount_from <= base <= section.amount_to:
                return base * section.percent / 100.0
        return 0.0


class SaleCommissionSection_1(models.Model):
    _name = "sale.commission.section_1"
    _description = "Секция комиссии"

    commission_id = fields.Many2one("sale.commission", string="Комиссия")
    amount_from = fields.Float(string="От")
    amount_to = fields.Float(string="До")
    percent = fields.Float(string="Процент", required=True)

    @api.constrains("amount_from", "amount_to")
    def _check_amounts(self):
        for section in self:
            if section.amount_to < section.amount_from:
                raise exceptions.ValidationError(
                    _("Нижний предел не может быть больше верхнего.")
                )
