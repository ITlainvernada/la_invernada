odoo.define('dimabe_manufacturing.barcode_manager', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var barcode_handler = AbstractField.extend({
        class: 'o_barcode_handler',
        tagName: 'input',
        supportedFieldTypes: ['char'],
        events: {
            'click .o_barcode_manager': 'manager'
        },
        init: function () {
            this._super.apply(this, arguments);
            var confirmed_serial = arguments[2].data.confirmed_serial;
            if (confirmed_serial) {
                var self = this;
                this._rpc({
                    'model': 'mrp.workorder',
                    'method': 'process_serial_by_barcode',
                    'args': [[self.res_id], confirmed_serial]
                }).then(value => {
                    self.do_action(value);
                    console.log(self);
                })
            }
        },
        _renderEdit: function () {

        },
        destroy: function () {
            this._super();
        }
    })
    fieldRegistry.add('barcode_manager', barcode_handler)
})