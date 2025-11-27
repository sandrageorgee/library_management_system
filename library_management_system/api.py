import frappe
import json
import base64


# BULK IMPORT 
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



 # GET ALL BOOKS  (List API)
@frappe.whitelist(allow_guest=False)
def get_books(limit=50):
    books = frappe.get_all(
        "Book",
        fields=["name", "title", "author", "isbn", "quantity", "available_quantity"],
        limit=limit
    )
    return books



#  SEARCH BOOKS (TITLE or AUTHOR)
@frappe.whitelist(allow_guest=False)
def search_books(query: str):
    if not query:
        return []

    query = f"%{query}%"

    results = frappe.db.sql(
        """
        SELECT name, title, author, isbn, quantity, available_quantity
        FROM `tabBook`
        WHERE title LIKE %s OR author LIKE %s
        LIMIT 20
        """,
        (query, query),
        as_dict=True
    )

    return results



# CREATE A  BOOK (API)
@frappe.whitelist(allow_guest=False)
def create_book(data: str):
    try:
        data = json.loads(data)

        doc = frappe.get_doc({
            "doctype": "Book",
            "title": data["title"],
            "author": data["author"],
            "isbn": data.get("isbn"),
            "quantity": data["quantity"],
            "available_quantity": data["available_quantity"],
            "category": data.get("category"),
            "description": data.get("description")
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "name": doc.name}

    except Exception as e:
        return {"status": "error", "message": str(e)}



# UPDATE EXISTING BOOK

@frappe.whitelist(allow_guest=False)
def update_book(name: str, data: str):
    try:
        data = json.loads(data)

        doc = frappe.get_doc("Book", name)

        # Update fields dynamically
        for key, value in data.items():
            if hasattr(doc, key):
                doc.set(key, value)

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "updated": name}

    except Exception as e:
        return {"status": "error", "message": str(e)}



#  DELETE BOOK

@frappe.whitelist(allow_guest=False)
def delete_book(name: str):
    try:
        frappe.delete_doc("Book", name, ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "deleted": name}
    except Exception as e:
        return {"status": "error", "message": str(e)}
