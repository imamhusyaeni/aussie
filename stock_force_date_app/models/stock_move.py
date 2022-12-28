# -*- coding: utf-8 -*-

import time
import pytz
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockMove(models.Model):
	_inherit = 'stock.move'

	def _action_done(self, cancel_backorder=False):
		force_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
			for move in self:
				if move.picking_id:
					if move.picking_id.force_date:
						force_date = move.picking_id.force_date
					else:
						force_date = move.picking_id.scheduled_date
				if move.scrapped==True:
					scrap_id = self.env['stock.scrap'].search([('name', '=', move.reference)])
					if scrap_id:
						if scrap_id.force_date:
							force_date = scrap_id.force_date
						else:
							force_date = scrap_id.date_done
				# if move.raw_material_production_id:
				# 	force_date = move.raw_material_production_id.mrp_date
				# if move.production_id:
				# 	force_date = move.production_id.mrp_date

		res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)

		if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
			if force_date:
				if isinstance(force_date, str) == True:
					force_date = datetime.strptime(force_date, "%Y-%m-%d %H:%M:%S")
				user_tz = self.env.user.tz or pytz.utc
				local = pytz.timezone(user_tz)
				local_date = pytz.utc.localize(force_date).astimezone(local)
				user_date = local_date.replace(tzinfo=None)

				for move in res:
					move.write({'date':force_date})
					if move.move_line_ids:
						for move_line in move.move_line_ids:
							move_line.write({'date':force_date})
					curr=move.purchase_line_id.currency_id.id
					company_curr=move.company_id.currency_id.id
					if move.account_move_ids:
						for account_move in move.account_move_ids:
							account_move.write({'date':user_date})
							# if move.inventory_id:
							# 	account_move.write({'ref':move.inventory_id.name})
							if curr!=False:
								if curr!=company_curr:
									cur_rate = self._get_new_rates(self.company_id, force_date)
									for aml in account_move.line_ids:
										debit=aml.debit
										credit=aml.credit
										if debit>0:
											new_debit=round(1/cur_rate*aml.amount_currency,2)
											sql_query="""Update account_move_line set debit=%s,balance=%s where id=%s
												"""
											self.env.cr.execute(sql_query,(new_debit,new_debit,aml.id,))
										elif credit>0:
											new_credit=round(1/cur_rate*aml.amount_currency,2)
											sql_query="""Update account_move_line set credit=-1*%s,balance=%s where id=%s
												"""
											self.env.cr.execute(sql_query,(new_credit,new_credit,aml.id,))
									sql_query="""Update account_move set amount_total=%s,amount_total_signed=%s where id=%s;
										Update stock_valuation_layer set unit_cost=%s/quantity,value=%s,remaining_value=%s where stock_move_id=%s;
										"""
									self.env.cr.execute(sql_query,(new_debit,new_debit,account_move.id,new_debit,new_debit,new_debit,move.id,))
    										

		return res

	def _get_new_rates(self, company, date):
		query = """SELECT r.rate FROM res_currency_rate r WHERE r.name <= %s
					AND r.company_id = %s ORDER BY r.company_id, r.name DESC LIMIT 1
				"""
		self._cr.execute(query, (date, company.id,))
		currency_rates = self._cr.fetchone()[0]
		return currency_rates


