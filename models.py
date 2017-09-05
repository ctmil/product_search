# -#- coding: utf-8 -#-

from openerp import tools, models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import except_orm, ValidationError
from StringIO import StringIO
import urllib2, httplib, urlparse, gzip, requests, json
import openerp.addons.decimal_precision as dp
import logging
import datetime
import time
from openerp.fields import Date as newdate
from datetime import datetime,date,timedelta
import re

#def fuzzyfinder(user_input, collection):
#	suggestions = []
#	pattern = '.*'.join(user_input)
#	regex = re.compile(pattern)
#	index = 0
#	for item in collection:
#		match = regex.search(item)
#		if match:
#			#suggestions.append(item)
#			suggestions.append(index)
#		index = index + 1
#	return suggestions


class sale_order(models.Model):
        _inherit = 'sale.order'

	searchbox = fields.Char('Productos a Buscar')
	inventory_available = fields.Boolean('Con stock',default=False)
	product_ids = fields.One2many(comodel_name='sale.order.product_search',inverse_name='order_id')

	@api.model
	def fuzzyfinder(self,user_input, collection):
		suggestions = []
		pattern = '.*'.join(user_input)
		regex = re.compile(pattern)
		index = 0
		for item in collection:
			match = regex.search(item)
			if match:
				#suggestions.append(item)
				suggestions.append(index)
			index = index + 1
		return suggestions

	@api.multi
	def add_products(self):
		self.ensure_one()
		for product in self.product_ids:
			if product.selected:
				line_data = self.env['sale.order.line'].product_id_change(
			                self.pricelist_id.id,
			                product.product_id.id,
			                qty=1,
			                partner_id=self.partner_id.id)
			        val = {
			                'product_uom_qty': 1,
		        	        'order_id': self.id,
			                'product_id': product.product_id.id or False,
			                'product_uom': line_data['value'].get('product_uom'),
			                'price_unit': line_data['value'].get('price_unit'),
		                	'tax_id': [(6, 0, line_data['value'].get('tax_id'))],
			            }
		                self.env['sale.order.line'].create(val)
		self.clear_products()


	@api.multi
	def clear_products(self):
		self.ensure_one()
		self.searchbox = ''
		self.inventory_available = False
		for product in self.product_ids:
			product.unlink()

	@api.multi
	def product_searchbox(self):
		#import pdb;pdb.set_trace()
		self.ensure_one()
		product_collection = []
		id_collection = []
		if self.searchbox:
			#sql = "select a.id,b.id,b.name from product_product a inner join product_template b on a.product_tmpl_id = b.id where upper(b.name) like '%" + \
			#	self.searchbox.upper() + "%'"
			products = self.env['product.product'].search([('sale_ok','=',True)])
			for product in products:
				if product.name:
					product_collection.append(product.name.upper())
					id_collection.append(product.id)
			# import pdb;pdb.set_trace()
			#product_ids  = self.env['sale.order'].fuzzyFinder(self.searchbox,product_collection)
			suggestions = []
			pattern = '.*'.join(self.searchbox.upper())
			regex = re.compile(pattern)
			index = 0
			product_ids = []
			for item in product_collection:
				match = regex.search(item)
				if match:
				#suggestions.append(item)
					product_ids.append(id_collection[index])
				index = index + 1
			#import pdb;pdb.set_trace()
					
			for product_id in product_ids:
				product = self.env['product.product'].browse(product_id)
				if product:
					vals = {
						'order_id': self.id,
						'product_id': product_id 
						}
					if self.inventory_available and product.qty_available > 0:	
						line_id = self.env['sale.order.product_search'].create(vals)
					if not self.inventory_available:	
						line_id = self.env['sale.order.product_search'].create(vals)
			#sql = "select a.id,b.id,b.name from product_product a inner join product_template b on a.product_tmpl_id = b.id where '"+ \
			#		self.searchbox + "' % name or '" + self.searchbox + "' % detalles or '" + self.searchbox + "' % modelo"
			#	
			#self.env.cr.execute(sql)
			#for a_id, b_id, b_name in self.env.cr.fetchall():
			#	vals = {
			#		'order_id': self.id,
			#		'product_id': a_id 
			#		}
			#	product = self.env['product.product'].browse(a_id)
			#	if self.inventory_available and product.qty_available > 0:	
			#		line_id = self.env['sale.order.product_search'].create(vals)
			#	if not self.inventory_available:	
			#		line_id = self.env['sale.order.product_search'].create(vals)
	

class sale_order_product_search(models.TransientModel):
	_name = 'sale.order.product_search'
	
	order_id = fields.Many2one('sale.order',readonly=True)
	product_id = fields.Many2one('product.product',readonly=True)
	lst_price = fields.Float('Precio',related='product_id.lst_price',readonly=True)
	qty_available = fields.Float('Inventario',related='product_id.qty_available',readonly=True)
	detalles = fields.Char('Detalles',related='product_id.detalles',readonly=True)
	modelo = fields.Char('Modelo',related='product_id.modelo',readonly=True)
	selected = fields.Boolean('Seleccionado',default=False)	
