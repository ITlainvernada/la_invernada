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


    //
    // var AbstractField = require('web.AbstractField');
    // var fieldRegistry = require('web.field_registry');
    // var concurrency = require('web.concurrency');
    // var BarcodeEvents = require('barcodes.BarcodeEvents');
    // var core = require('web.core');
    // var FormController = require('web.FormController');
    //
    // FormController.include({
    //     custom_events: _.extend({}, FormController.prototype.custom_events, {
    //        initBarCode: '_initBarcode'
    //     }),
    //     init: function () {
    //         this._super.apply(this, arguments);
    //         this.barcodeMutex = new concurrency.Mutex();
    //         this.watchBarcode();
    //     },
    //     destroy: function () {
    //         this.stopBarcode();
    //         this._super();
    //     },
    //     _initBarcode: function (event) {
    //       event.stopPropagation();
    //       var name = event.data.name;
    //       console.log(name);
    //       this.disableAutofocus = true;
    //     },
    //     watchBarcode: function () {
    //         core.bus.on('confirmed_serial', this, this._confirmed_serial);
    //     },
    //     stopBarcode: function () {
    //         core.bus.off('confirmed_serial', this, this._confirmed_serial);
    //     },
    //     _confirmed_serial: function () {
    //         var self = this;
    //         return this.barcodeMutex.exec(function () {
    //             console.log(self);
    //         })
    //     },
    // })
    //
    // // var barcode_handler = AbstractField.extend({
    // //     class: 'o_barcode_handler',
    // //     tagName: 'input',
    // //     supportedFieldTypes: ['char'],
    // //     events: {
    // //         'click .o_barcode_manager': 'manager'
    // //     },
    // //     init: function () {
    // //         this._super.apply(this, arguments);
    // //         this.barcodeMutex = new concurrency.Mutex();
    // //         this.watchBarcode();
    // //     },
    // //     _render: function () {
    // //         this.$el.text(this.value);
    // //     },
    // //     destroy: function () {
    // //         this._super();
    // //     },
    // //     watchBarcode: function () {
    // //         core.bus.on('confirmed_serial', this, this.confirmed_serial);
    // //     },
    // //     confirmed_serial: function (barcode, target) {
    // //         return this.barcodeMutex.exec(function () {
    // //             var prefixed = _
    // //         });
    // //     }
    // // })
    // // fieldRegistry.add('barcode_manager', barcode_handler)
})