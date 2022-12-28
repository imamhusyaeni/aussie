# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.osv import expression


class StockInventory(models.Model):
	_inherit = 'stock.inventory'

	force_date = fields.Datetime(string="Force Date")

	@api.onchange('force_date')
	def onchange_forcedate(self):
		self.accounting_date=self.force_date

	def _get_quantities(self):
		tz = self.env.user.tz
		if tz==False:
			raise UserError(('Timezone must be set first..'))
		# """Return quantities group by product_id, location_id, lot_id, package_id and owner_id

		# :return: a dict with keys as tuple of group by and quantity as value
		# :rtype: dict
		# """
		# self.ensure_one()
		# if self.location_ids:
		# 	domain_loc = [('id', 'child_of', self.location_ids.ids)]
		# else:
		# 	domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]
		# locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

		# domain = [('company_id', '=', self.company_id.id),
		# 			('quantity', '!=', '0'),
		# 			('location_id', 'in', locations_ids)]
		# if self.prefill_counted_quantity == 'zero':
		# 	domain.append(('product_id.active', '=', True))

		# if self.product_ids:
		# 	domain = expression.AND([domain, [('product_id', 'in', self.product_ids.ids)]])

		# fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'quantity:sum']
		# group_by = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id']

		# quants = self.env['stock.quant'].read_group(domain, fields, group_by, lazy=False)
		# cek= {(
		# 	quant['product_id'] and quant['product_id'][0] or False,
		# 	quant['location_id'] and quant['location_id'][0] or False,
		# 	quant['lot_id'] and quant['lot_id'][0] or False,
		# 	quant['package_id'] and quant['package_id'][0] or False,
		# 	quant['owner_id'] and quant['owner_id'][0] or False):
		# 	quant['quantity'] for quant in quants
		# }
		if self.force_date:
			tot_loc=0
			if self.location_ids:
				for location in self.location_ids:
					loc=location.id
					tot_loc+=1
			else:
				raise UserError('Location can not be empty')
			if tot_loc>1:
				raise UserError('Location must be from one location only')
			if self.product_ids:
				tot_prod=0
				for product in self.product_ids:
					product_id=product.id
					tot_prod+=1
					if tot_prod>1:
						raise UserError('Product must be for one product only')
				
				# sql_query="""select t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id,sum(t1.quantity) as quantity from (
				# 	select product_id,location_dest_id as location_id,lot_id,package_id,owner_id,sum(qty_done) as quantity from stock_move_line where 
				# 	state='done' and location_dest_id = %s and product_id=%s
				# 	and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
				# 	group by product_id,location_dest_id,lot_id,package_id,owner_id,qty_done
				# 	union
				# 	select product_id,location_id,lot_id,package_id,owner_id,sum(qty_done)*-1 as quantity from stock_move_line where 
				# 	state='done' and location_id = %s and product_id=%s
				# 	and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
				# 	group by product_id,location_id,lot_id,package_id,owner_id,qty_done) t1 
				# 	group by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
				# 	having sum(t1.quantity)>0
				# 	order by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
				# 	"""
				
				# self.env.cr.execute(sql_query,(loc,product_id,self.force_date,loc,product_id,self.force_date,))
				# quants = self.env.cr.dictfetchall()

				sql_query="""select t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id,sum(t1.quantity) as quantity from (
					select product_id,location_dest_id as location_id,lot_id,package_id,owner_id,sum(qty_done) as quantity from stock_move_line where 
					state='done' and location_dest_id = %s and product_id=%s
					and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
					group by product_id,location_dest_id,lot_id,package_id,owner_id,qty_done) t1 
					group by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					having sum(t1.quantity)>0
					order by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					"""
				
				self.env.cr.execute(sql_query,(loc,product_id,self.force_date))
				quants_in = self.env.cr.dictfetchall()

				sql_query1="""select t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id,sum(t1.quantity) as quantity from (
					select product_id,location_id as location_id,lot_id,package_id,owner_id,sum(qty_done) as quantity from stock_move_line where 
					state='done' and location_id = %s and product_id=%s
					and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
					group by product_id,location_id,lot_id,package_id,owner_id,qty_done) t1 
					group by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					having sum(t1.quantity)>0
					order by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					"""
				
				self.env.cr.execute(sql_query1,(loc,product_id,self.force_date))
				quants_out = self.env.cr.dictfetchall()
				quants_out[0]['quantity'] = quants_in[0]['quantity'] - quants_out[0]['quantity']

				return {(
					quant['product_id'],
					quant['location_id'],
					quant['lot_id'],
					quant['package_id'],
					quant['owner_id']):
					quant['quantity'] for quant in quants_out
				}
			else:
				# sql_query="""select t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id,sum(t1.quantity) as quantity from (
				# 	select product_id,location_dest_id as location_id,lot_id,package_id,owner_id,sum(qty_done) as quantity from stock_move_line where 
				# 	state='done' and location_dest_id = %s 
				# 	and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
				# 	group by product_id,location_dest_id,lot_id,package_id,owner_id,qty_done
				# 	union
				# 	select product_id,location_id,lot_id,package_id,owner_id,sum(qty_done)*-1 as quantity from stock_move_line where 
				# 	state='done' and location_id = %s 
				# 	and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
				# 	group by product_id,location_id,lot_id,package_id,owner_id,qty_done) t1 
				# 	inner join product_product t2 on t1.product_id=t2.id
				# 	inner join product_template t3 on t2.product_tmpl_id=t3.id
				# 	where t3.type='product'
				# 	group by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
				# 	having sum(t1.quantity)>0
				# 	order by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
				# 	"""
				# self.env.cr.execute(sql_query,(loc,self.force_date,loc,self.force_date,))
				# quants = self.env.cr.dictfetchall()

				sql_query="""select t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id,sum(t1.quantity) as quantity from (
					select product_id,location_dest_id as location_id,lot_id,package_id,owner_id,sum(qty_done) as quantity from stock_move_line where 
					state='done' and location_dest_id = %s
					and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
					group by product_id,location_dest_id,lot_id,package_id,owner_id,qty_done) t1 
					group by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					having sum(t1.quantity)>0
					order by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					"""
				
				self.env.cr.execute(sql_query,(loc,self.force_date))
				quants_in = self.env.cr.dictfetchall()

				sql_query1="""select t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id,sum(t1.quantity) as quantity from (
					select product_id,location_id as location_id,lot_id,package_id,owner_id,sum(qty_done) as quantity from stock_move_line where 
					state='done' and location_id = %s
					and cast(date ::timestamp at time zone 'UTC' AT time zone '""" + tz + """' as DATE) <= %s
					group by product_id,location_id,lot_id,package_id,owner_id,qty_done) t1 
					group by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					having sum(t1.quantity)>0
					order by t1.product_id,t1.location_id,t1.lot_id,t1.package_id,t1.owner_id
					"""
				
				self.env.cr.execute(sql_query1,(loc,self.force_date))
				quants_out = self.env.cr.dictfetchall()
				for quant_out in quants_out:
					for quant_in in quants_in:
						if quant_out['product_id'] == quant_in['product_id']:
							quant_out['quantity'] = quant_in['quantity'] - quant_out['quantity']

				return {(
					quant['product_id'],
					quant['location_id'],
					quant['lot_id'],
					quant['package_id'],
					quant['owner_id']):
					quant['quantity'] for quant in quants_out
				}				
		res=super(StockInventory,self)._get_quantities()
		return res
		
		

	def action_validate(self):
        # do actual processing
		res = super(StockInventory,self).action_validate()
        # overwrite date field where applicable
		if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
			if self.force_date:
				sql_query="""Update stock_inventory set date=%s where id=%s;
					Update stock_inventory_line set inventory_date=%s where inventory_id=%s;
					"""
				self.env.cr.execute(sql_query,(self.force_date,self.id,self.force_date,self.id,))
				for move in self.move_ids:
					sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
						"""
					self.env.cr.execute(sql_query,(self.force_date,move.id,))
		return res


		
