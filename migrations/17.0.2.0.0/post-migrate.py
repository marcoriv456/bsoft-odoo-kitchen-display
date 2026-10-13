from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Bootstrap persistent tickets when upgrading an existing installation."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env["pos.order"].search([
        ("state", "in", ["draft", "paid", "done", "invoiced"]),
    ])
    orders._bsoft_sync_kitchen_tickets()
