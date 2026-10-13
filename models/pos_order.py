from odoo import api, fields, models, _
from odoo.exceptions import AccessError

KITCHEN_STATES = [
    ("new", "Pendiente"), ("preparing", "Preparando"),
    ("ready", "Listo"), ("served", "Entregado"), ("cancelled", "Cancelado")
]

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    kitchen_state = fields.Selection(KITCHEN_STATES, default="new", copy=False, index=True, string="Estado de cocina")
    kitchen_station_id = fields.Many2one("bsoft.kitchen.station", string="Estación", index=True, copy=False)
    kitchen_started_at = fields.Datetime(copy=False)
    kitchen_ready_at = fields.Datetime(copy=False)
    kitchen_note = fields.Char(string="Nota de cocina", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if not line.kitchen_station_id:
                line.kitchen_station_id = line._bsoft_get_station()
        lines._bsoft_notify()
        return lines

    def write(self, vals):
        result = super().write(vals)
        if set(vals) & {"kitchen_state", "kitchen_station_id", "product_id", "qty", "kitchen_note"}:
            self._bsoft_notify()
        return result

    def _bsoft_get_station(self):
        self.ensure_one()
        stations = self.env["bsoft.kitchen.station"].sudo().search([("active", "=", True)], order="sequence,id")
        product_categories = self.product_id.pos_categ_ids
        config = self.order_id.config_id
        for station in stations:
            if station.pos_config_ids and config not in station.pos_config_ids:
                continue
            if not station.category_ids or product_categories & station.category_ids:
                return station
        return False

    def _bsoft_notify(self):
        # Notification is a hint; clients refresh their authorized snapshot after receiving it.
        try:
            self.env["bus.bus"]._sendone("bsoft_kitchen_display", "bsoft_kitchen_update", {"ids": self.ids})
        except Exception:
            pass

    def action_bsoft_set_kitchen_state(self, state):
        if state not in dict(KITCHEN_STATES):
            raise AccessError(_("Estado de cocina no válido."))
        user = self.env.user
        groups = [
            "bsoft_kitchen_display.group_kitchen_cook",
            "bsoft_kitchen_display.group_kitchen_manager",
            "bsoft_kitchen_display.group_kitchen_admin",
        ]
        if not any(user.has_group(group) for group in groups):
            raise AccessError(_("No tienes permiso para cambiar el estado de cocina."))
        vals = {"kitchen_state": state}
        if state == "preparing":
            vals["kitchen_started_at"] = fields.Datetime.now()
        elif state == "ready":
            vals["kitchen_ready_at"] = fields.Datetime.now()
        self.write(vals)
        return True
