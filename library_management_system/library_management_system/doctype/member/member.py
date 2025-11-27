import frappe
from frappe.model.document import Document

class Member(Document):
    def validate(self):
        # basic sanity
        if self.total_debt is None:
            self.total_debt = 0

        if self.total_debt > 500:
            frappe.throw("Member debt cannot exceed Rs. 500")
