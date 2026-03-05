import sys
import os

# Ensure Micro Ocr Module exists
if not frappe.db.exists("Module Def", "Micro Ocr"):
    module = frappe.new_doc("Module Def")
    module.module_name = "Micro Ocr"
    module.app_name = "micro_ocr"
    module.custom = 0
    module.insert(ignore_permissions=True)
    frappe.db.commit()

# Update OCR Settings
doc = frappe.get_doc("DocType", "OCR Settings")
doc.module = "Micro Ocr"
# Force save
doc.save(ignore_permissions=True)
frappe.db.commit()

print("OCR Settings Module updated to Micro Ocr")

# Let's also check if there's a Workspace we can add it to, or just print success.
frappe.destroy()
