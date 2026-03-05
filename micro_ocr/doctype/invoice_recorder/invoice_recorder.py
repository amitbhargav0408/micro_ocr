# Copyright (c) 2026, amit bhargav and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import os
import re

class InvoiceRecorder(Document):
    def on_update(self):
        if self.invoice_file and self.ocr_status != "Completed":
            # Proceed to extract text
            self.extract_data()

    def extract_data(self):
        # Fetch the file absolute path
        file_doc = frappe.get_all("File", filters={"file_url": self.invoice_file}, fields=["name", "file_name", "file_url"])
        if not file_doc:
            return
            
        file_path = frappe.get_site_path("public", self.invoice_file.lstrip('/'))
        if not os.path.exists(file_path):
            file_path = frappe.get_site_path("private", self.invoice_file.lstrip('/'))
            
        if not os.path.exists(file_path):
            frappe.msgprint("File not found on disk for OCR.")
            return

        ext = file_path.split('.')[-1].lower()
        
        try:
            import base64
            import json
            from huggingface_hub import InferenceClient
            
            # Use user-provided Inference Key
            api_key = None
            try:
                ocr_settings = frappe.get_doc("OCR Settings")
                api_key = ocr_settings.get_password("hugging_face_api_key")
            except Exception:
                pass
            
            if not api_key:
                frappe.throw("Hugging Face API key not found in OCR Settings.")
                
            api_key = api_key.strip()
            if not api_key.startswith("hf_"):
                frappe.throw(f"Invalid Hugging Face API key provided. It must start with 'hf_'. Found: '{api_key[:5]}...'")
            
            client = InferenceClient(token=api_key)
            
            images_base64 = []
            
            if ext == 'pdf':
                from pdf2image import convert_from_path
                images = convert_from_path(file_path)
                for img in images:
                    from io import BytesIO
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    images_base64.append(base64.b64encode(buffered.getvalue()).decode('utf-8'))
            else:
                with open(file_path, "rb") as image_file:
                    images_base64.append(base64.b64encode(image_file.read()).decode('utf-8'))
                    
            if not images_base64:
                self.db_set("ocr_status", "Failed - Could not convert image")
                return
                
            # Process the first page to get all data
            b64_image = images_base64[0]
            
            prompt = """
            Extract all invoice information from this image.
            Return ONLY a valid JSON object matching this structure exactly (no markdown formatting, no code blocks):
            {
              "supplier": "Company Name",
              "invoice_number": "INV-123",
              "date": "YYYY-MM-DD",
              "due_date": "YYYY-MM-DD",
              "address": "Full Address",
              "base_total": 0.0,
              "cgst_amount": 0.0,
              "sgst_amount": 0.0,
              "igst_amount": 0.0,
              "amount": 0.0,
              "currency": "USD/INR/etc",
              "items": [
                {
                  "item_name": "Name",
                  "description": "Desc",
                  "hsn_sac": "12345",
                  "received_qty": 1.0,
                  "discount": 0.0,
                  "rate": 100.0,
                  "amount": 100.0
                }
              ]
            }
            """
            
            completion = client.chat.completions.create(
                model="Qwen/Qwen2.5-VL-7B-Instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            res_text = completion.choices[0].message.content
            
            # Clean JSON formatting artifacts
            res_text = res_text.strip()
            if res_text.startswith("```json"): res_text = res_text[7:]
            if res_text.startswith("```"): res_text = res_text[3:]
            if res_text.endswith("```"): res_text = res_text[:-3]
            
            try:
                data = json.loads(res_text.strip())
            except Exception as e:
                frappe.log_error(f"Failed to parse JSON from LLM: {res_text}", "OCR JSON Error")
                self.db_set("ocr_status", "Failed - LLM returned invalid JSON")
                return
            
            # Map fields to DB
            if data.get("supplier"): self.db_set("supplier", str(data["supplier"])[:140])
            if data.get("invoice_number"): self.db_set("invoice_number", str(data["invoice_number"])[:140])
            if data.get("address"): self.db_set("address", str(data["address"])[:1000])
            if data.get("currency"): self.db_set("currency", str(data["currency"])[:10])
            
            for num_field in ["base_total", "cgst_amount", "sgst_amount", "igst_amount", "amount"]:
                if data.get(num_field):
                    try:
                        # try converting strings like "$ 191.08" by keeping numbers
                        val_str = str(data[num_field])
                        val_cleaned = re.sub(r'[^\d.]', '', val_str)
                        if val_cleaned:
                            self.db_set(num_field, float(val_cleaned))
                    except: pass
                    
            for date_field in ["date", "due_date"]:
                if data.get(date_field):
                    try:
                        from frappe.utils.data import getdate
                        self.db_set(date_field, getdate(data[date_field]))
                    except: pass
                    
            if data.get("items"):
                for idx, item in enumerate(data["items"]):
                    if not isinstance(item, dict): continue
                    
                    try:
                        rate_val = float(re.sub(r'[^\d.]', '', str(item.get("rate") or "0")))
                    except: rate_val = 0.0
                    
                    try:
                        amt_val = float(re.sub(r'[^\d.]', '', str(item.get("amount") or "0")))
                    except: amt_val = 0.0
                    
                    try:
                        qty_val = float(re.sub(r'[^\d.]', '', str(item.get("received_qty") or "1")))
                    except: qty_val = 1.0
                    
                    try:
                        disc_val = float(re.sub(r'[^\d.]', '', str(item.get("discount") or "0")))
                    except: disc_val = 0.0
                    
                    self.append("items", {
                        "item_name": str(item.get("item_name", f"Item {idx+1}"))[:140],
                        "description": str(item.get("description", str(item.get("item_name", "")))),
                        "hsn_sac": str(item.get("hsn_sac", ""))[:140],
                        "received_qty": qty_val,
                        "discount": disc_val,
                        "rate": rate_val,
                        "amount": amt_val
                    })
            
            # Flush changes to DB including the Child Table arrays
            self.ocr_status = "Completed"
            self.save(ignore_permissions=True)
            
            frappe.msgprint("LLM Extraction Successful")
            
        except frappe.exceptions.ValidationError:
            pass # Ignore validation errors on save loop
        except Exception as e:
            self.db_set("ocr_status", f"Failed - {str(e)[:50]}")
            frappe.log_error(f"Invoice LLM error: {e}", "OCR Error")

    def parse_and_set_fields(self, text):
        pass # Now handled natively inside extract_data by LLM formatting

@frappe.whitelist()
def export_to_excel(docname):
    import csv
    import os

    doc = frappe.get_doc("Invoice Recorder", docname)
    
    file_name = f"{doc.name}_export.csv"
    file_path = frappe.get_site_path("public", "files", file_name)
    
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Name", "Invoice Number", "Supplier", "Company", "Address", "Date", "Due Date", 
            "Base Total", "CGST", "SGST", "IGST", "Grand Total", "Currency", "OCR Status",
            "Item Name", "HSN/SAC", "Qty", "Discount", "Rate", "Amount"
        ])
        
        # Safely get field values 
        invoice_num = getattr(doc, "invoice_number", "")
        company = getattr(doc, "company", "")
        address = getattr(doc, "address", "")
        due_date = getattr(doc, "due_date", "")
        base_tot = getattr(doc, "base_total", "")
        cgst = getattr(doc, "cgst_amount", "")
        sgst = getattr(doc, "sgst_amount", "")
        igst = getattr(doc, "igst_amount", "")
        currency = getattr(doc, "currency", "")
        
        parent_row = [
            doc.name, invoice_num, doc.supplier, company, address, doc.date, due_date, 
            base_tot, cgst, sgst, igst, doc.amount, currency, doc.ocr_status
        ]
        
        items = getattr(doc, "items", [])
        if not items:
            writer.writerow(parent_row + ["", "", "", "", "", ""])
        else:
            for item in items:
                writer.writerow(parent_row + [
                    item.item_name, getattr(item, 'hsn_sac', ''), 
                    getattr(item, 'received_qty', ''), getattr(item, 'discount', ''), getattr(item, 'rate', ''), 
                    getattr(item, 'amount', '')
                ])
    
    # Return URL (csv can be opened in Excel)
    return f"/files/{file_name}"
