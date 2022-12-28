odoo.define('bi_pos_stock.db', function(require) {
	"use strict";

	var PosDB = require('point_of_sale.DB');

	PosDB.DB = PosDB.include({
        get_product_by_category: function(category_id){
			var product_ids  = this.product_by_category_id[category_id];
			var list = [];
			if (product_ids) {
				for (var i = 0, len = product_ids.length; i < len; i++) {
					list.push(this.product_by_id[product_ids[i]]);
				}
				console.log('total = '+len)
			}
			return list;
		},
	});

});
