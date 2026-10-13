from odoo import http, fields
from odoo.http import request

class BsoftKitchenController(http.Controller):
    def _allowed(self):
        user = request.env.user
        return any(user.has_group(g) for g in [
            "bsoft_kitchen_display.group_kitchen_cook",
            "bsoft_kitchen_display.group_kitchen_manager",
            "bsoft_kitchen_display.group_kitchen_admin",
        ])

    @http.route("/bsoft_kitchen_display/data", type="json", auth="user")
    def kitchen_data(self, station_id=None):
        if not self._allowed():
            return {"error": "No tienes permiso para consultar la pantalla."}
        domain = [
            ("order_id.state", "in", ["draft", "paid", "done", "invoiced"]),
            ("kitchen_state", "in", ["new", "preparing", "ready"]),
        ]
        if station_id:
            domain.append(("kitchen_station_id", "=", int(station_id)))
        lines = request.env["pos.order.line"].sudo().search(domain, order="id desc", limit=300)
        rows = []
        for line in lines:
            order = line.order_id
            rows.append({
                "id": line.id,
                "order_name": order.pos_reference or order.name or str(order.id),
                "table": order.table_id.name if order.table_id else "",
                "product": line.full_product_name or line.product_id.display_name,
                "qty": line.qty,
                "note": line.customer_note or line.kitchen_note or "",
                "state": line.kitchen_state or "new",
                "station_id": line.kitchen_station_id.id or False,
                "station_name": line.kitchen_station_id.name or "",
                "created_at": fields.Datetime.to_string(order.date_order) if order.date_order else "",
                "started_at": fields.Datetime.to_string(line.kitchen_started_at) if line.kitchen_started_at else "",
            })
        stations = request.env["bsoft.kitchen.station"].sudo().search([("active", "=", True)], order="sequence,name")
        return {"lines": rows, "stations": [
            {"id": s.id, "name": s.name, "warning": s.warning_minutes,
             "critical": s.critical_minutes, "sound": s.sound_enabled} for s in stations
        ]}

    @http.route("/bsoft_kitchen_display/set_state", type="json", auth="user")
    def set_state(self, line_id, state):
        if not self._allowed():
            return {"error": "No tienes permiso para cambiar estados."}
        line = request.env["pos.order.line"].browse(int(line_id)).exists()
        if not line:
            return {"error": "La línea no existe."}
        line.action_bsoft_set_kitchen_state(state)
        return {"ok": True}
