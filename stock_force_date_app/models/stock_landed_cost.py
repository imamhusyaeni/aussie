# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def button_validate(self):
        # do actual processing
        res = super(StockLandedCost,self).button_validate()
        # overwrite date field where applicable
        if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
            sql_query="""Update stock_valuation_layer set create_date=%s where stock_landed_cost_id=%s
                """
            self.env.cr.execute(sql_query,(self.date,self.id,))
        return res
    
    
