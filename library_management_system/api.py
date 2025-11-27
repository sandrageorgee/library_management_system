import frappe
import json
import base64

@frappe.whitelist(allow_guest=False)
def bulk_import_books(payload_b64: str):
    try:
        # Decode Base64 → JSON
        json_bytes = base64.b64decode(payload_b64)
        data = json.loads(json_bytes.decode("utf-8"))

        created = []

        for item in data:
            doc = frappe.get_doc({
                "doctype": "Book",
                "title": item["title"],
                "author": item["author"],
                "isbn": item["isbn"],
                "quantity": item["quantity"],
                "available_quantity": item["available_quantity"]
            })
            doc.insert(ignore_permissions=True)
            created.append(doc.name)

        frappe.db.commit()

        return {"status": "success", "created": created}

    except Exception as e:
        return {"status": "error", "message": str(e)}
