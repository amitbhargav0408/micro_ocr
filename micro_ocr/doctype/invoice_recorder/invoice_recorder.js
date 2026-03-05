// Copyright (c) 2026, amit bhargav and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Recorder", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Export to Excel'), function () {
                frappe.call({
                    method: "micro_ocr.micro_ocr.doctype.invoice_recorder.invoice_recorder.export_to_excel",
                    args: {
                        docname: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            window.open(r.message);
                        }
                    }
                });
            }, __('Actions'));
        }
    },
});
