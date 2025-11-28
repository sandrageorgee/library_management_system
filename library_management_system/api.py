import frappe
import json
import base64
from datetime import datetime, timedelta



# ============================================================
#                     BOOK APIs
# ============================================================


# BULK IMPORT 
@frappe.whitelist(allow_guest=False)
def bulk_import_books(payload_b64: str):
    try:
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




# GET ALL BOOKS
@frappe.whitelist(allow_guest=False)
def get_books(limit=50):
    return frappe.get_all(
        "Book",
        fields=["name", "title", "author", "isbn", "quantity", "available_quantity"],
        limit=limit
    )



# SEARCH BOOKS
@frappe.whitelist(allow_guest=False)
def search_books(query: str):
    if not query:
        return []

    query = f"%{query}%"

    return frappe.db.sql(
        """
        SELECT name, title, author, isbn, quantity, available_quantity
        FROM `tabBook`
        WHERE title LIKE %s OR author LIKE %s
        LIMIT 20
        """,
        (query, query),
        as_dict=True
    )



# CREATE BOOK
@frappe.whitelist(allow_guest=False)
def create_book(data: str):
    try:
        data = json.loads(data)

        doc = frappe.get_doc({
            "doctype": "Book",
            **data
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "name": doc.name}

    except Exception as e:
        return {"status": "error", "message": str(e)}



# UPDATE BOOK
@frappe.whitelist(allow_guest=False)
def update_book(name: str, data: str):
    try:
        data = json.loads(data)
        doc = frappe.get_doc("Book", name)

        for key, value in data.items():
            if hasattr(doc, key):
                doc.set(key, value)

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "updated": name}

    except Exception as e:
        return {"status": "error", "message": str(e)}



# DELETE BOOK
@frappe.whitelist(allow_guest=False)
def delete_book(name: str):
    try:
        frappe.delete_doc("Book", name, ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "deleted": name}
    except Exception as e:
        return {"status": "error", "message": str(e)}




# ============================================================
#                     MEMBER APIs
# ============================================================


@frappe.whitelist()
def create_member(data: str):
    data = json.loads(data)
    doc = frappe.get_doc({"doctype": "Member", **data})
    doc.insert()
    frappe.db.commit()
    return {"status": "success", "name": doc.name}


@frappe.whitelist()
def update_member(name: str, data: str):
    data = json.loads(data)
    doc = frappe.get_doc("Member", name)

    for key, value in data.items():
        doc.set(key, value)

    doc.save()
    frappe.db.commit()
    return {"status": "success", "updated": name}


@frappe.whitelist()
def delete_member(name: str):
    frappe.delete_doc("Member", name)
    frappe.db.commit()
    return {"status": "success", "deleted": name}


@frappe.whitelist()
def get_members():
    return frappe.get_all(
        "Member",
        fields=["name", "full_name", "email", "outstanding_dues", "debt_limit", "active"]
    )


@frappe.whitelist()
def search_members(query: str):
    return frappe.get_all(
        "Member",
        or_filters=[
            ["full_name", "like", f"%{query}%"],
            ["email", "like", f"%{query}%"]
        ],
        fields=["name", "full_name", "email"]
    )




# ============================================================
#                  TRANSACTIONS (ISSUE / RETURN)
# ============================================================


@frappe.whitelist()
def issue_book(member: str, book: str, date_issued: str):

    # Validate
    if not frappe.db.exists("Member", member):
        frappe.throw(f"Member '{member}' not found")

    if not frappe.db.exists("Book", book):
        frappe.throw(f"Book '{book}' not found")

    book_doc = frappe.get_doc("Book", book)

    if book_doc.available_quantity <= 0:
        frappe.throw("No available copies to issue.")

    # Calculate due date (14 days)
    date_issued_obj = datetime.strptime(date_issued, "%Y-%m-%d")
    due_date = date_issued_obj + timedelta(days=14)

    # Create Book Transaction
    tx = frappe.get_doc({
        "doctype": "Book Transaction",
        "member": member,
        "book": book,
        "type": "Issue",
        "date_issued": date_issued,
        "due_date": due_date.strftime("%Y-%m-%d")
    })
    tx.insert(ignore_permissions=True)

    # Reduce available copies
    book_doc.available_quantity -= 1
    book_doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "status": "success",
        "transaction": tx.name,
        "due_date": due_date.strftime("%Y-%m-%d")
    }




# RETURN BOOK
@frappe.whitelist()
def return_book(member: str, book: str, return_date: str):
    try:
        # Find last issue transaction
        txn = frappe.get_all(
            "Book Transaction",
            filters={"member": member, "book": book, "type": "Issue"},
            fields=["name", "due_date"],
            order_by="creation desc",
            limit=1
        )

        if not txn:
            frappe.throw("No issued book found to return.")

        txn = txn[0]
        due_date = frappe.utils.getdate(txn["due_date"])
        return_dt = frappe.utils.getdate(return_date)

        # Calculate fine
        fine = 0
        if return_dt > due_date:
            late_days = (return_dt - due_date).days
            fine = late_days * 10  # 10 LE per day

        # Create return transaction
        ret = frappe.get_doc({
            "doctype": "Book Transaction",
            "member": member,
            "book": book,
            "type": "Return",
            "return_date": return_date,
            "fine_amount": fine
        })
        ret.insert(ignore_permissions=True)

        # Update book availability
        book_doc = frappe.get_doc("Book", book)
        book_doc.available_quantity += 1
        book_doc.save(ignore_permissions=True)

        # Apply fine to member
        member_doc = frappe.get_doc("Member", member)

        if fine > 0:
            member_doc.outstanding_dues += fine

        member_doc.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "status": "success",
            "transaction": ret.name,
            "fine": fine
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
