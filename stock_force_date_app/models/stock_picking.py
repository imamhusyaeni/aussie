# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    force_date = fields.Datetime(string="Force Date")

    @api.depends('state', 'move_lines', 'move_lines.state', 'move_lines.package_level_id', 'move_lines.move_line_ids.package_level_id')
    def button_validate(self):
        # do actual processing
        res = super(StockPicking,self).button_validate()
        # overwrite date field where applicable
        if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
    	    if self.force_date:        
                for move in self.move_ids_without_package:
                    sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                        """
                    self.env.cr.execute(sql_query,(self.force_date,move.id,))
                    # svl_obj=self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id)])
                    # if svl_obj:
                    #     svl_obj.write({'create_date':self.force_date})
        return res
        