import frappe

def create_doctype():
    frappe.flags.in_install = True
    doctype_name = "Invoice Recorder"
    if not frappe.db.exists("DocType", doctype_name):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": doctype_name,
            "module": "Micro Ocr",
            "custom": 0,
            "autoname": "format:INV-REC-{YYYY}-{MM}-{####}",
            "fields": [
                {
                    "fieldname": "invoice_file",
                    "label": "Invoice File",
                    "fieldtype": "Attach Image",
                    "reqd": 1
                },
                {
                    "fieldname": "supplier",
                    "label": "Supplier",
                    "fieldtype": "Data",
                    "reqd": 0
                },
                {
                    "fieldname": "date",
                    "label": "Date",
                    "fieldtype": "Date",
                    "reqd": 0
                },
                {
                    "fieldname": "amount",
                    "label": "Amount",
                    "fieldtype": "Currency",
                    "reqd": 0
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "export": 1
                }
            ]
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"{doctype_name} DocType created successfully.")
    else:
        print(f"{doctype_name} DocType already exists.")

