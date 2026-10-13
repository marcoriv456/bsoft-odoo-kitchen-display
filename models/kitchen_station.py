from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class BsoftKitchenStation(models.Model):
    _name = "bsoft.kitchen.station"
    _description = "BSOFT Kitchen Station"
    _order = "sequence, name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    category_ids = fields.Many2many("pos.category", string="Categorías POS")
    pos_config_ids = fields.Many2many("pos.config", string="Puntos de venta")
    warning_minutes = fields.Integer(default=10)
    critical_minutes = fields.Integer(default=20)
    sound_enabled = fields.Boolean(default=True)

    @api.constrains("warning_minutes", "critical_minutes")
    def _check_times(self):
        for rec in self:
            if rec.warning_minutes < 0 or rec.critical_minutes < rec.warning_minutes:
                raise ValidationError(_("Los tiempos deben ser positivos y el crítico mayor o igual al de aviso."))
