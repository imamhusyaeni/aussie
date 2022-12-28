# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    force_date = fields.Datetime(string="Force Date")

    def action_validate(self):
        # do actual processing
        res = super(StockScrap,self).action_validate()
        # overwrite date field where applicable
        if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
    	    if self.force_date:
                move_obj=self.env['stock.move'].search([('reference','=',self.name)])
                if move_obj:        
                    sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                        """
                    self.env.cr.execute(sql_query,(self.force_date,move_obj.id,))
        return res
    
    
