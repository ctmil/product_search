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

class sale_order(models.Model):
        _inherit = 'sale.order'

	searchbox = fields.Char('Productos a Buscar')
	product_ids = fields.One2many(comodel_name='sale.order.product_search',inverse_name='order_id')

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
		for product in self.product_ids:
			product.unlink()

	@api.multi
	def product_searchbox(self):
		#import pdb;pdb.set_trace()
		self.ensure_one()
		if self.searchbox:
			sql = "select a.id,b.id,b.name from product_product a inner join product_template b on a.product_tmpl_id = b.id where upper(b.name) like '%" + \
				self.searchbox.upper() + "%'"
			self.env.cr.execute(sql)
			for a_id, b_id, b_name in self.env.cr.fetchall():
				vals = {
					'order_id': self.id,
					'product_id': a_id 
					}	
				line_id = self.env['sale.order.product_search'].create(vals)	
	

class sale_order_product_search(models.TransientModel):
	_name = 'sale.order.product_search'
	
	order_id = fields.Many2one('sale.order',readonly=True)
	product_id = fields.Many2one('product.product',readonly=True)
	lst_price = fields.Float('Precio',related='product_id.lst_price',readonly=True)
	qty_available = fields.Float('Inventario',related='product_id.qty_available',readonly=True)
	selected = fields.Boolean('Seleccionado',default=False)	
