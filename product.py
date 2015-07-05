# -*- coding: utf-8 -*-
from openerp import fields, models, api
import openerp.addons.decimal_precision as dp


class product_template(models.Model):
    _inherit = 'product.template'

    @api.model
    def get_currency_id(self):
        price_type_obj = self.env['product.price.type']
        price_type_ids = price_type_obj.search([('field', '=', 'standard_price')])
        if not price_type_ids.currency_id:
            return self.env.user.company_id.currency_id
        return price_type_ids.currency_id

    cost_price_currency_id = fields.Many2one(
        'res.currency', 'Cost Price Currency',
        required=True, default=get_currency_id,
        help="Currency used for the Currency Cost Price."
        )
    cia_currency_cost_price = fields.Float(
        'Company Currency Cost Price',
        digits=dp.get_precision('Product Price'),
        # ver Product Price si se reemplaza por algo
        compute='get_cia_currency_cost_price',
        help="Cost price on company currency (local currency) at current exchange rate",
        )

    @api.multi
    @api.depends('standard_price', 'cost_price_currency_id')
    def get_cia_currency_cost_price(self):
        company_currency = self.env.user.company_id.currency_id
        for product in self:
            if product.cost_price_currency_id != company_currency:
                cia_currency_cost_price = product.cost_price_currency_id.compute(
                    product.standard_price, company_currency)
            else:
                cia_currency_cost_price = product.standard_price
            product.cia_currency_cost_price = cia_currency_cost_price


    def _price_get(self, cr, uid, products, ptype='standard_price', context=None):
        if not context:
            context = {}
        res = super(product_template, self)._price_get(
            cr, uid, products, ptype=ptype, context=context)
        if ptype == 'standard_price':
            pricetype_obj = self.pool.get('product.price.type')
            price_type_id = pricetype_obj.search(
                cr, uid, [('field', '=', ptype)])[0]
            price_type_currency_id = pricetype_obj.browse(
                cr, uid, price_type_id).currency_id.id
            for product in products:
                if product.cost_price_currency_id.id != price_type_currency_id:
                    res[product.id] = self.pool.get('res.currency').compute(
                        cr, uid, product.cost_price_currency_id.id,
                        price_type_currency_id, res[product.id],
                        context=context)
        return res
