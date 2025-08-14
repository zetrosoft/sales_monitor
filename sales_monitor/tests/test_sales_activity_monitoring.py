import frappe
import unittest
from frappe.utils import getdate, now_datetime

class TestSalesActivityMonitoring(unittest.TestCase):
    def setUp(self):
        # Clean up any existing test data
        frappe.db.sql("DELETE FROM `tabSales Activity Log`")
        frappe.db.sql("DELETE FROM `tabSales Visit Plan Item`")
        frappe.db.sql("DELETE FROM `tabSales Visit Plan`")
        frappe.db.commit()

        # Create a dummy User
        if not frappe.db.exists("User", "test_sales@example.com"):
            self.test_user = frappe.get_doc({
                "doctype": "User",
                "email": "test_sales@example.com",
                "first_name": "Test",
                "last_name": "Sales",
                "enabled": 1,
                "new_password": "password", # Set a dummy password
                "roles": [{"role": "Sales User"}] # Assign a relevant role
            }).insert(ignore_permissions=True)
        else:
            self.test_user = frappe.get_doc("User", "test_sales@example.com")

        # Create a dummy Sales Person (Employee)
        if not frappe.db.exists("Employee", "Test Sales Person"):
            self.sales_person = frappe.get_doc({
                "doctype": "Employee",
                "employee_name": "Test Sales Person",
                "user_id": self.test_user.name # Link to the created user
            }).insert(ignore_permissions=True)
        else:
            self.sales_person = frappe.get_doc("Employee", "Test Sales Person")

        # Create a dummy Customer
        if not frappe.db.exists("Customer", "Test Customer"):
            self.customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "Test Customer"
            }).insert(ignore_permissions=True)
        else:
            self.customer = frappe.get_doc("Customer", "Test Customer")

        # Create a dummy Sales Visit Plan
        self.sales_visit_plan = frappe.get_doc({
            "doctype": "Sales Visit Plan",
            "sales_person": self.sales_person.name,
            "planned_visit_date": getdate(),
            "status": "Planned",
            "visit_plan_details": []
        }).insert(ignore_permissions=True)

        # Create a dummy Sales Visit Plan Item
        self.sales_visit_plan_item = frappe.get_doc({
            "doctype": "Sales Visit Plan Item",
            "parent": self.sales_visit_plan.name,
            "parenttype": "Sales Visit Plan",
            "parentfield": "visit_plan_details",
            "customer": self.customer.name,
            "address": "Test Address",
            "visit_time": "10:00:00",
            "notes": "Initial notes",
            "status": "Planned"
        }).insert(ignore_permissions=True)

        # Link the item to the parent plan
        self.sales_visit_plan.append("visit_plan_details", {
            "customer": self.customer.name,
            "address": "Test Address",
            "visit_time": "10:00:00",
            "notes": "Initial notes",
            "status": "Planned"
        })
        self.sales_visit_plan.save(ignore_permissions=True)
        frappe.db.commit()

    def tearDown(self):
        # Clean up test data
        frappe.db.sql("DELETE FROM `tabSales Activity Log`")
        frappe.db.sql("DELETE FROM `tabSales Visit Plan Item`")
        frappe.db.sql("DELETE FROM `tabSales Visit Plan`")
        frappe.db.sql("DELETE FROM `tabEmployee` WHERE name = 'Test Sales Person'")
        frappe.db.sql("DELETE FROM `tabCustomer` WHERE name = 'Test Customer'")
        frappe.db.sql("DELETE FROM `tabUser` WHERE email = 'test_sales@example.com'") # Clean up dummy user
        frappe.db.commit()