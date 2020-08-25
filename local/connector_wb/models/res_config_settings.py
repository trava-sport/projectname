from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wb_client_secret = fields.Char("Client_key_wb", config_parameter='wildberries_client_secret', default='')
    
