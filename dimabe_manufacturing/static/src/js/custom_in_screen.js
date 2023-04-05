odoo.define('dimabe_manufacturing.barcode_manager', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var rpc = require('web.rpc')

    FormController.include({
        init: function () {
            this._super.apply(this, arguments);
        },
        _barcodeScanned: function (barcode, target) {
            var self = this
            rpc.query({
                model: this.modelName,
                method: 'process_serial_by_barcode',
                args: [barcode, this.initialState.data.id]
            }).then(res => {
                if (!res.ok && !res.name) {
                    self.do_warn(res.message);
                } else {
                    self.reload.bind(self);
                }

            })
        }
    })
})