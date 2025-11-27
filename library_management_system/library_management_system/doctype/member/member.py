import frappe
from frappe.model.document import Document

class Member(Document):

    def validate(self):

        # Rule 1: Outstanding dues cannot be negative

        if self.outstanding_dues < 0:
            frappe.throw("Outstanding dues cannot be negative.")

        
        # Rule 2: Debt limit must be >= 0
        
        if self.debt_limit < 0:
            frappe.throw("Debt limit cannot be negative.")

        
        # Rule 3: Outstanding dues must not exceed debt limit
    
        if self.outstanding_dues > self.debt_limit:
            frappe.throw(
                f"Outstanding dues ({self.outstanding_dues}) exceed allowed debt limit ({self.debt_limit})."
            )

        
        # Rule 4: Debt limit cannot exceed ₹500 
        
        if self.debt_limit > 500:
            frappe.throw("Debt limit cannot exceed ₹500.")

        
        # Rule 5: Email must be unique
        
        if self.email:
            exists = frappe.db.exists(
                "Member",
                {"email": self.email, "name": ["!=", self.name]}
            )
            if exists:
                frappe.throw("A member with this email already exists.")

        
        # Rule 6: Auto-format email to lowercase
        
        if self.email:
            self.email = self.email.strip().lower()

        
        # Rule 7: Full Name is required
        
        if not self.full_name or self.full_name.strip() == "":
            frappe.throw("Member Full Name is required.")

        
        
