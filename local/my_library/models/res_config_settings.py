from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_self_borrow = fields.Boolean(string="Self borrow", implied_group='my_library.group_self_borrow')
    

class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    group_release_dates = fields.Boolean(
        "Manage book release dates",
        group='base.group_user',
        implied_group='my_library.group_release_dates',
    )
    module_note = fields.Boolean("Install Notes app")