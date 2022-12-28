# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero

class StockQuant(models.Model):
	_inherit = 'stock.quant'

	
	def _apply_inventory(self):
		move_vals = []
		if not self.user_has_groups('stock.group_stock_manager'):
			raise UserError(_('Only a stock manager can validate an inventory adjustment.'))
		for quant in self:
			# Create and validate a move so that the quant matches its `inventory_quantity`.
			if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
				move_vals.append(
					quant._get_inventory_move_values(quant.inventory_diff_quantity,
													quant.product_id.with_company(quant.company_id).property_stock_inventory,
													quant.location_id))
			else:
				move_vals.append(
					quant._get_inventory_move_values(-quant.inventory_diff_quantity,
													quant.location_id,
													quant.product_id.with_company(quant.company_id).property_stock_inventory,
													out=True))
		moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
		moves._action_done()
		for quant in self:
			force_date = quant.accounting_date or fields.Date.today()
			for move in moves:
				for move_line in move.move_line_ids:
					move_line.update({'date':force_date})
				for valuation in move.stock_valuation_layer_ids:
					valuation.update({'create_date':force_date})
					sql_query="""update stock_valuation_layer set create_date=%s where id=%s
						"""
					self.env.cr.execute(sql_query,(force_date,valuation.id,))
					for am in valuation.account_move_id:
						am.update({'date':force_date})
		self.location_id.write({'last_inventory_date': fields.Date.today()})
		date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
		for quant in self:
			quant.inventory_date = date_by_location[quant.location_id]
		self.write({'inventory_quantity': 0, 'user_id': False})
		self.write({'inventory_diff_quantity': 0})
