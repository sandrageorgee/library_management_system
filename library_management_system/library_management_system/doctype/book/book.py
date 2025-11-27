import frappe
import re
from frappe.model.document import Document

class Book(Document):
    def validate(self):

        #Validate Title
        if not self.title or not self.title.strip():
            frappe.throw("Book title cannot be empty.")


        #Validate Author

        if not self.author or not self.author.strip():
            frappe.throw("Author name cannot be empty.")

        # Validate ISBN Format
        
        if self.isbn:
            # Allow only digits and hyphens (000-00-0000)
            if not re.match(r"^[0-9\-]+$", self.isbn):
                frappe.throw("ISBN may only contain digits and hyphens.")
            
            # ISBN must be unique
            exists = frappe.db.exists(
                "Book",
                {
                    "isbn": self.isbn,
                    "name": ["!=", self.name]   # Exclude current record when editing
                }
            )
            if exists:
                frappe.throw("A book with this ISBN already exists.")

        
        # Quantity Validations
        
        if not isinstance(self.quantity, int):
            frappe.throw("Total Quantity must be an integer.")

        if not isinstance(self.available_quantity, int):
            frappe.throw("Available Quantity must be an integer.")

        # Quantity must be positive or zero
        if self.quantity < 0:
            frappe.throw("Total Quantity cannot be negative.")

        # Available cannot exceed total
        if self.available_quantity > self.quantity:
            frappe.throw("Available Quantity cannot be greater than Total Quantity.")

        # Auto-fill Available Quantity
        
        if self.available_quantity is None:
            self.available_quantity = self.quantity

     
