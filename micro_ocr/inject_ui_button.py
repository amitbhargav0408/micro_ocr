import frappe

def inject_client_script():
    script_name = "Job Requisition Resume Extractor"
    
    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
    else:
        doc = frappe.new_doc("Client Script")
        doc.dt = "Job Requisition"
        doc.name = script_name
        doc.module = "Micro Ocr" # Custom app name
        doc.enabled = 1

    js_code = """
frappe.ui.form.on('Job Requisition', {
    refresh(frm) {
        // Add a button to extract attached resumes
        if (!frm.is_new()) {
            frm.add_custom_button(__('Extract Attached Resumes'), function() {
                frappe.call({
                    method: "micro_ocr.api.extract_resumes_to_candidates",
                    args: {
                        job_requisition_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Extracting candidates via AI..."),
                    callback: function(r) {
                        if (r.message && r.message.status === "success") {
                            frappe.msgprint({
                                title: __('Success'),
                                indicator: 'green',
                                message: r.message.message
                            });
                            // Reload the form to show new child table records
                            frm.reload_doc();
                        } else {
                            if (r.message && r.message.errors) {
                                frappe.msgprint({
                                    title: __('Error'),
                                    indicator: 'red',
                                    message: r.message.errors.join('<br>')
                                });
                            } else {
                                frappe.msgprint(__('Failed to extract candidates. Check Error Logs.'));
                            }
                        }
                    }
                });
            }, __('AI Actions'));
            
            // Highlight the button
            frm.change_custom_button_type('Extract Attached Resumes', null, 'primary', __('AI Actions'));
        }
    }
});
"""
    doc.script = js_code
    doc.save()
    frappe.db.commit()
    print("Injected Client Script successfully.")

if __name__ == "__main__":
    frappe.init(site="core")
    frappe.connect()
    inject_client_script()
