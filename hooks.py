def post_init_hook(env):
    """Create durable tickets for unfinished legacy POS lines during upgrade."""
    orders = env["pos.order"].search([
        ("state", "in", ["draft", "paid", "done", "invoiced"]),
    ])
    orders._bsoft_sync_kitchen_tickets()
