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
            ("state", "in", ["new", "preparing", "ready"]),
        ]
        if station_id:
            domain.append(("station_id", "=", int(station_id)))
        tickets = request.env["bsoft.kitchen.ticket"].sudo().search(domain, order="ordered_at desc, id desc", limit=300)
        rows = []
        for ticket in tickets:
            order = ticket.order_id
            rows.append({
                "id": ticket.id,
                "order_name": order.pos_reference or order.name or str(order.id),
                "table": order.table_id.name if order.table_id else "",
                "product": ticket.product_name,
                "qty": ticket.qty,
                "note": ticket.note or "",
                "state": ticket.state,
                "station_id": ticket.station_id.id or False,
                "station_name": ticket.station_id.name or "",
                "created_at": fields.Datetime.to_string(ticket.ordered_at),
                "started_at": fields.Datetime.to_string(ticket.started_at) if ticket.started_at else "",
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
        ticket = request.env["bsoft.kitchen.ticket"].sudo().browse(int(line_id)).exists()
        if not ticket:
            return {"error": "La línea no existe."}
        ticket.with_context(bsoft_kitchen_actor_id=request.env.uid).action_bsoft_set_state(state)
        return {"ok": True}
