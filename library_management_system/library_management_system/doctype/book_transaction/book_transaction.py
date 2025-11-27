import frappe
from frappe.model.document import Document

class BookTransaction(Document):

    def validate(self):
        # auto-set dates
        if self.transaction_type == "Issue" and not self.date_issued:
            self.date_issued = frappe.utils.today()

        if self.transaction_type == "Issue" and not self.due_date:
            # default: 14 days after issue
            self.due_date = frappe.utils.add_days(self.date_issued, 14)

    def on_submit(self):
        if self.transaction_type == "Issue":
            self._issue_book()
        elif self.transaction_type == "Return":
            self._return_book()

    def on_cancel(self):
        # simple reverse logic
        if self.transaction_type == "Issue":
            self._reverse_issue()
        elif self.transaction_type == "Return":
            self._reverse_return()

    # ---------------- internal helpers ----------------

    def _issue_book(self):
        book = frappe.get_doc("Book", self.book)
        member = frappe.get_doc("member", self.member)

        if book.available_qty <= 0:
            frappe.throw("No available copies for this book.")

        # enforce 500 Rs debt limit (future-friendly if you later add charges)
        if (member.total_debt or 0) + (self.fine_amount or 0) > 500:
            frappe.throw("Member will exceed Rs. 500 debt limit with this transaction.")

        # update quantities
        book.available_qty -= 1
        book.save()

        # optionally add a row in Member's outstanding_books
        self._add_outstanding_row(member)
        member.save()

    def _return_book(self):
        book = frappe.get_doc("Book", self.book)
        member = frappe.get_doc("member", self.member)

        # increase stock back
        book.available_qty += 1
        book.save()

        # mark corresponding row as Returned
        self._mark_row_returned(member)
        member.save()

    def _reverse_issue(self):
        # if you cancel an Issue, undo the stock + table row
        book = frappe.get_doc("Book", self.book)
        member = frappe.get_doc("member", self.member)

        book.available_qty += 1
        book.save()

        # delete any outstanding row for this book+member
        member.outstanding_books = [
            row for row in member.outstanding_books
            if row.book != self.book
        ]
        member.save()

    def _reverse_return(self):
        # opposite of _return_book
        book = frappe.get_doc("Book", self.book)
        member = frappe.get_doc("member", self.member)

        book.available_qty -= 1
        book.save()

        # mark status back to Issued
        for row in member.outstanding_books:
            if row.book == self.book and row.status == "Returned":
                row.status = "Issued"
                break
        member.save()

    def _add_outstanding_row(self, member):
        row = member.append("outstanding_books", {})
        row.book = self.book
        row.date_issued = self.date_issued
        row.due_date = self.due_date
        row.status = "Issued"
        row.fine = self.fine_amount or 0

    def _mark_row_returned(self, member):
        # set return info in first matching outstanding row
        for row in member.outstanding_books:
            if row.book == self.book and row.status == "Issued":
                row.status = "Returned"
                row.return_date = self.return_date or frappe.utils.today()
                row.fine = self.fine_amount or row.fine
                break
