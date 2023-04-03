odoo.define('dimabe_manufacturing.barcode_manager', function (require) {
    "use strict";

    var FormController = require('web.FormController');

    FormController.include({
        init: function () {
            this._super.apply(this, arguments);
        },
        _barcodeScanned: function (barcode, target) {
            this._rpc({
                model: this.modelName,
                method: 'process_serial_by_barcode',
                args: [[this.initialState.data.id], barcode]
            }).then(res => {
                this.do_action(res)
            })
        }
    })
})