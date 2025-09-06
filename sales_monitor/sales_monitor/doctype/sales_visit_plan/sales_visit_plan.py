import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate, now_datetime

class SalesVisitPlan(Document):
    def before_insert(self):
        if not self.naming_series:
            self.naming_series = "SPV-.YYYY.-.######"
        self.name = make_autoname(self.naming_series)

    def on_update(self):
        pass

    def before_submit(self):
        pass
        

    def on_cancel(self):
        # Allow cancellation only if status is not 'Completed'
        if self.status == "Completed":
            frappe.throw("Cannot cancel a Completed Sales Visit Plan.")
        self.status = "Cancelled"

    def on_submit(self):
        # Set the status to Planned after successful submission
        self.status = "Planned"
        for item in self.visit_plan_details:
            frappe.db.set_value("Sales Visit Plan Item", item.name, "status", "Planned")

    def validate(self):
        if not self.visit_plan_details:
            frappe.throw("At least one Visit Plan Detail is required.")

        # Ensure sales_id is populated when sales_person is selected
        if self.sales_person and not self.sales_id:
            employee_user_id = frappe.db.get_value("Employee", self.sales_person, "user_id")
            if employee_user_id:
                self.sales_id = employee_user_id

        # Populate employee_name from linked Employee
        if self.sales_person:
            self.employee_name = frappe.db.get_value("Employee", self.sales_person, "employee_name")

        # Calculate planned_visit_count
        self.planned_visit_count = len(self.visit_plan_details)

        

        # Ensure sales_person is mandatory
        if not self.sales_person:
            frappe.throw("Sales Person is mandatory.")

        # Ensure planned_visit_date is mandatory
        if not self.planned_visit_date:
            frappe.throw("Planned Visit Date is mandatory.")

        # Ensure sales_id is read-only after initial population
        if not self.is_new() and self.sales_id != frappe.db.get_value("Employee", self.sales_person, "user_id"):
            frappe.throw("Sales ID cannot be changed.")

@frappe.whitelist()
def cancel_sales_visit_plan(name):
    """Cancels a Sales Visit Plan document."""
    doc = frappe.get_doc("Sales Visit Plan", name)
    doc.cancel()

@frappe.whitelist()
def get_list_context(context):
    context.add_fields(["name", "planned_visit_date", "employee_name", "status", "planned_visit_count"])
    context.get_list = get_sales_visit_plan_list

def get_sales_visit_plan_list(doctype, filters, start, page_len, order_by):
    # Fetch main Sales Visit Plan documents
    sales_visit_plans = frappe.get_list(
        doctype,
        filters=filters,
        start=start,
        page_length=page_len,
        order_by=order_by,
        fields=["name", "planned_visit_date", "sales_person", "employee_name", "status", "planned_visit_count"]
    )

    for plan in sales_visit_plans:
        # Ensure employee_name is populated if sales_person is set
        if plan.sales_person and not plan.employee_name:
            plan.employee_name = frappe.db.get_value("Employee", plan.sales_person, "employee_name")

        # Fetch associated Sales Visit Plan Items
        items = frappe.get_all(
            "Sales Visit Plan Item",
            filters={
                "parent": plan.name,
                "parenttype": "Sales Visit Plan",
                "parentfield": "visit_plan_details"
            },
            fields=["name"], # Only need name to count
            as_list=True # Get as list for counting
        )
        plan.planned_visit_count = len(items) # Count the items

    return sales_visit_plans