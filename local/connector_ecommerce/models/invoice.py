# -*- coding: utf-8 -*-
# © 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    
    def action_invoice_paid(self):
        res = super(AccountMove, self).action_invoice_paid()
        for record in self:
            self._event('on_invoice_paid').notify(record)
        return res

    
    def invoice_validate(self):
        res = super(AccountMove, self).invoice_validate()
        for record in self:
            self._event('on_invoice_validated').notify(record)
        return res
