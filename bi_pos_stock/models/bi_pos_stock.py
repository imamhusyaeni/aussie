# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import Warning
import random
from odoo.tools import float_is_zero
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError


class pos_config(models.Model):
	_inherit = 'pos.config'

	def _get_default_location(self):
		return self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1).lot_stock_id
	
	pos_display_stock = fields.Boolean(string='Display Stock in POS')
	pos_stock_type = fields.Selection([('onhand', 'Qty on Hand'), ('incoming', 'Incoming Qty'), ('outgoing', 'Outgoing Qty'), ('available', 'Qty Available')], string='Stock Type', help='Seller can display Different stock type in POS.')
	pos_allow_order = fields.Boolean(string='Allow POS Order When Product is Out of Stock')
	pos_deny_order = fields.Char(string='Deny POS Order When Product Qty is goes down to')   
	
	show_stock_location = fields.Selection([
		('all', 'All Warehouse'),
		('specific', 'Current Session Warehouse'),
		], string='Show Stock Of', default='all')

	stock_location_id = fields.Many2one(
		'stock.location', string='Stock Location',
		domain=[('usage', '=', 'internal')], required=True, default=_get_default_location)

		
class pos_order(models.Model):
	_inherit = 'pos.order'

	location_id = fields.Many2one(
		comodel_name='stock.location',
		related='config_id.stock_location_id',
		string="Location", store=True,
		readonly=True,
	)


class stock_quant(models.Model):
	_inherit = 'stock.quant'

	def get_stock_location_qty(self, location):
		res = {}
		product_ids = self.env['product.product'].search([])
		for product in product_ids:
			quants = self.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			if len(quants) > 1:
				quantity = 0.0
				for quant in quants:
					quantity += quant.quantity
				res.update({product.id : quantity})
			else:
				res.update({product.id : quants.quantity})
		return [res]

	def get_products_stock_location_qty(self, location,products):
		res = {}
		product_ids = self.env['product.product'].sudo().browse(products)
		for product in product_ids:
			if product.bom_ids and product.bom_ids.type == 'phantom':
				components = []
				stock_avail = 0
				for component in product.bom_ids.bom_line_ids:
					quants = self.env['stock.quant'].sudo().search([('product_id', '=', component.product_id.id),('location_id', '=', location['id'])])
					if len(quants) > 1:
						quantity = 0.0
						for quant in quants:
							quantity += quant.quantity
						components.append([component.product_id.id, int(quantity/component.product_qty)])
					else:
						components.append([component.product_id.id, int(quants.quantity/component.product_qty)])

				for data in components:
					if stock_avail > 0:
						if data[1] < stock_avail:
							stock_avail = data[1]
					else:
						stock_avail = data[1]

				res.update({product.id : stock_avail})
			else:
				quants = self.env['stock.quant'].sudo().search([('product_id', '=', product.id),('location_id', '=', location['id'])])
				if len(quants) > 1:
					quantity = 0.0
					for quant in quants:
						quantity += quant.quantity
					res.update({product.id : quantity})
				else:
					res.update({product.id : quants.quantity})

		return [res]

	def get_single_product(self,product, location):
		res = []
		pro = self.env['product.product'].browse(product)
		if pro.bom_ids and pro.bom_ids.type == 'phantom':
			components = []
			stock_avail = 0
			for component in pro.bom_ids.bom_line_ids:
				quants = self.env['stock.quant'].search([('product_id', '=', component.product_id.id),('location_id', '=', location['id'])])
				if len(quants) > 1:
					quantity = 0.0
					for quant in quants:
						quantity += quant.quantity
					components.append([component.product_id.id, int(quantity/component.product_qty)])
				else:
					components.append([component.product_id.id, int(quants.quantity/component.product_qty)])

			for data in components:
					if stock_avail > 0:
						if data[1] < stock_avail:
							stock_avail = data[1]
					else:
						stock_avail = data[1]

			res.append([pro.id, stock_avail])
		else:
			quants = self.env['stock.quant'].search([('product_id', '=', pro.id),('location_id', '=', location['id'])])
			if len(quants) > 1:
				quantity = 0.0
				for quant in quants:
					quantity += quant.quantity
				res.append([pro.id, quantity])
			else:
				res.append([pro.id, quants.quantity])

		return res


class product(models.Model):
	_inherit = 'product.product'
	
	available_quantity = fields.Float('Available Quantity')

	def get_stock_location_avail_qty(self, location,products):
		res = {}
		product_ids = self.env['product.product'].browse(products)
		for product in product_ids:
			if product.bom_ids and product.bom_ids.type == 'phantom':
				components = []
				stock_avail = 0
				for component in product.bom_ids.bom_line_ids:
					# quants = self.env['stock.quant'].search([('product_id', '=', component.product_id.id),('location_id', '=', location['id'])])
					sql_query_quants = """select * from stock_quant where product_id=%s and location_id=%s"""
					self._cr.execute(sql_query_quants, (component.product_id.id,location['id']))
					quants = self._cr.dictfetchall()

					# outgoing = self.env['stock.move'].search([('product_id', '=', component.product_id.id),('location_id', '=', location['id'])])
					sql_query_outgoing = """select * from stock_move where product_id=%s and location_id=%s"""
					self._cr.execute(sql_query_outgoing, (component.product_id.id,location['id']))
					outgoing = self._cr.dictfetchall()

					# incoming = self.env['stock.move'].search([('product_id', '=', component.product_id.id),('location_dest_id', '=', location['id'])])
					sql_query_incoming = """select * from stock_move where product_id=%s and location_dest_id=%s"""
					self._cr.execute(sql_query_incoming, (component.product_id.id,location['id']))
					incoming = self._cr.dictfetchall()

					qty=0.0
					product_qty = 0.0
					incoming_qty = 0.0
					if len(quants) > 1:
						for quant in quants:
							qty += quant['quantity']

						if len(outgoing) > 0:
							for quant in outgoing:
								if quant['state'] not in ['done','cancel']:
									product_qty += quant['product_qty']

						if len(incoming) > 0:
							for quant in incoming:
								if quant['state'] not in ['done']:
									incoming_qty += quant['product_qty']
							# component.product_id.available_quantity = qty-product_qty + incoming_qty
							components.append([(qty-product_qty + incoming_qty)/component.product_qty])
					else:
						if not quants:
							if len(outgoing) > 0:
								for quant in outgoing:
									if quant['state'] not in ['done','cancel']:
										product_qty += quant['product_qty']

							if len(incoming) > 0:
								for quant in incoming:
									if quant['state'] not in ['done']:
										incoming_qty += quant['product_qty']
							# component.product_id.available_quantity = qty-product_qty + incoming_qty
							components.append([(qty-product_qty + incoming_qty)/component.product_qty])
						else:
							if len(outgoing) > 0:
								for quant in outgoing:
									if quant['state'] not in ['done','cancel']:
										product_qty += quant['product_qty']

							if len(incoming) > 0:
								for quant in incoming:
									if quant['state'] not in ['done']:
										incoming_qty += quant['product_qty']
							# component.product_id.available_quantity = quants[0]['quantity'] - product_qty + incoming_qty
							components.append([(quants[0]['quantity'] - product_qty + incoming_qty)/component.product_qty])

				# for data in components:
				# 	if stock_avail > 0:
				# 		if data[1] < stock_avail:
				# 			stock_avail = data[1]
				# 	else:
				# 		stock_avail = data[1]
				if components:
					stock_avail = min(components)

				product.available_quantity = int(stock_avail[0])
				res.update({product.id : int(stock_avail[0])})

			else:
				# quants = self.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
				sql_query_quants = """select * from stock_quant where product_id=%s and location_id=%s"""
				self._cr.execute(sql_query_quants, (product.id,location['id']))
				quants = self._cr.dictfetchall()

				# outgoing = self.env['stock.move'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
				sql_query_outgoing = """select * from stock_move where product_id=%s and location_id=%s"""
				self._cr.execute(sql_query_outgoing, (product.id,location['id']))
				outgoing = self._cr.dictfetchall()

				# incoming = self.env['stock.move'].search([('product_id', '=', product.id),('location_dest_id', '=', location['id'])])
				sql_query_incoming = """select * from stock_move where product_id=%s and location_dest_id=%s"""
				self._cr.execute(sql_query_incoming, (product.id,location['id']))
				incoming = self._cr.dictfetchall()

				qty=0.0
				product_qty = 0.0
				incoming_qty = 0.0
				if len(quants) > 1:
					for quant in quants:
						qty += quant['quantity']

					if len(outgoing) > 0:
						for quant in outgoing:
							if quant['state'] not in ['done','cancel']:
								product_qty += quant['product_qty']

					if len(incoming) > 0:
						for quant in incoming:
							if quant['state'] not in ['done']:
								incoming_qty += quant['product_qty']
						product.available_quantity = qty-product_qty + incoming_qty
						res.update({product.id : qty-product_qty + incoming_qty})
				else:
					if not quants:
						if len(outgoing) > 0:
							for quant in outgoing:
								if quant['state'] not in ['done','cancel']:
									product_qty += quant['product_qty']

						if len(incoming) > 0:
							for quant in incoming:
								if quant['state'] not in ['done']:
									incoming_qty += quant['product_qty']
						product.available_quantity = qty-product_qty + incoming_qty
						res.update({product.id : qty-product_qty + incoming_qty})
					else:
						if len(outgoing) > 0:
							for quant in outgoing:
								if quant['state'] not in ['done','cancel']:
									product_qty += quant['product_qty']

						if len(incoming) > 0:
							for quant in incoming:
								if quant['state'] not in ['done']:
									incoming_qty += quant['product_qty']
						product.available_quantity = quants[0]['quantity'] - product_qty + incoming_qty
						res.update({product.id : quants[0]['quantity'] - product_qty + incoming_qty})
		return [res]
	

class StockPicking(models.Model):
	_inherit='stock.picking'

	@api.model
	def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
		"""We'll create some picking based on order_lines"""
		
		pickings = self.env['stock.picking']
		stockable_lines = lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding))
		if not stockable_lines:
			return pickings
		positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
		negative_lines = stockable_lines - positive_lines

		if positive_lines:
			pos_order = positive_lines[0].order_id
			location_id = pos_order.location_id.id
			vals = self._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
			positive_picking = self.env['stock.picking'].create(vals)
			positive_picking._create_move_from_pos_order_lines(positive_lines)
			try:
				with self.env.cr.savepoint():
					positive_picking._action_done()
			except (UserError, ValidationError):
				pass

			pickings |= positive_picking
		if negative_lines:
			if picking_type.return_picking_type_id:
				return_picking_type = picking_type.return_picking_type_id
				return_location_id = return_picking_type.default_location_dest_id.id
			else:
				return_picking_type = picking_type
				return_location_id = picking_type.default_location_src_id.id

			vals = self._prepare_picking_vals(partner, return_picking_type, location_dest_id, return_location_id)
			negative_picking = self.env['stock.picking'].create(vals)
			negative_picking._create_move_from_pos_order_lines(negative_lines)
			try:
				with self.env.cr.savepoint():
					negative_picking._action_done()
			except (UserError, ValidationError):
				pass
			pickings |= negative_picking
		return pickings