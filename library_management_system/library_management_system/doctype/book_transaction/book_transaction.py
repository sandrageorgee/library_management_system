import frappe
from frappe.model.document import Document

class BookTransaction(Document):

    def validate(self):
        book = frappe.get_doc("Book", self.book)
        member = frappe.get_doc("Member", self.member)

        # ISSUE LOGIC
        if self.type == "Issue":
            if book.available_quantity <= 0:
                frappe.throw("This book is out of stock.")

            if member.outstanding_dues >= member.debt_limit:
                frappe.throw("Member reached the debt limit and cannot issue more books.")

            book.available_quantity -= 1
            book.save()

            # Auto calculate due date (+14 days)
            if not self.due_date:
                self.due_date = frappe.utils.add_days(self.date_issued, 14)

        # RETURN LOGIC
        if self.type == "Return":
            if not self.return_date:
                frappe.throw("Return Date is required for a return.")

            book.available_quantity += 1
            book.save()

            return_date = frappe.utils.getdate(self.return_date)
            due_date = frappe.utils.getdate(self.due_date)

            if return_date > due_date:
                delay_days = (return_date - due_date).days
                self.fine_amount = delay_days * 10
                member.outstanding_dues += self.fine_amount
                member.save()
            else:
                self.fine_amount = 0


    def before_save(self):
        today = frappe.utils.getdate()

        due_date = frappe.utils.getdate(self.due_date) if self.due_date else None
        return_date = frappe.utils.getdate(self.return_date) if self.return_date else None

        # RETURN STATUS
        if self.type == "Return":
            if return_date and due_date and return_date > due_date:
                self.transaction_status = "Late Return"
            else:
                self.transaction_status = "Returned"

            # Ensure fine is calculated before saving
            if return_date and due_date and return_date > due_date:
                delay_days = (return_date - due_date).days
                self.fine_amount = delay_days * 10

                member = frappe.get_doc("Member", self.member)
                member.outstanding_dues += self.fine_amount
                member.save()
            else:
                self.fine_amount = 0

        else:
            # ISSUE STATUS
            if due_date and today > due_date:
                self.transaction_status = "Late"
            else:
                self.transaction_status = "Issued"

            # Auto daily fine if book is not returned
            if due_date and today > due_date and not self.return_date:
                late_days = (today - due_date).days
                self.fine_amount = late_days * 10

                member = frappe.get_doc("Member", self.member)
                member.outstanding_dues += 10
                member.save()


    # -----------------------------
    # NEW: UPDATE FINE EVERY SAVE
    # -----------------------------
    def on_update(self):
        # Recalculate fine on EVERY change
        if self.type == "Return" and self.return_date and self.due_date:
            return_date = frappe.utils.getdate(self.return_date)
            due_date = frappe.utils.getdate(self.due_date)

            if return_date > due_date:
                delay_days = (return_date - due_date).days
                self.fine_amount = delay_days * 10

                member = frappe.get_doc("Member", self.member)
                member.outstanding_dues += self.fine_amount
                member.save()
            else:
                self.fine_amount = 0

        # Also update fine for late issued books
        if self.type == "Issue" and self.due_date and not self.return_date:
            today = frappe.utils.getdate()
            due_date = frappe.utils.getdate(self.due_date)

            if today > due_date:
                late_days = (today - due_date).days
                self.fine_amount = late_days * 10

                member = frappe.get_doc("Member", self.member)
                member.outstanding_dues += 10
                member.save()
