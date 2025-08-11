import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate, now_datetime

class SalesVisitPlan(Document):
    def before_insert(self):
        # Set the naming_series field programmatically
        year_month = now_datetime().strftime("%Y%m")
        self.naming_series = f"SPV-{year_month}-" # Use hyphen for naming series

    def on_update(self):
        if self.docstatus == 1 and self.status == "Draft":
            self.status = "Planned"
            self.save()

    def on_cancel(self):
        # Allow cancellation only if status is not 'Completed'
        if self.status == "Completed":
            frappe.throw("Cannot cancel a Completed Sales Visit Plan.")
        self.status = "Cancelled"
        self.save()

    def validate(self):
        if not self.visit_plan_details:
            frappe.throw("At least one Visit Plan Detail is required.")

        # Ensure sales_id is populated when sales_person is selected
        if self.sales_person and not self.sales_id:
            employee_user_id = frappe.db.get_value("Employee", self.sales_person, "user_id")
            if employee_user_id:
                self.sales_id = employee_user_id

        # Ensure planned_visit_date is set to today's date on creation
        if self.is_new():
            self.planned_visit_date = nowdate()

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
def get_list_context(context):
    context.add_fields(["name", "sales_person", "planned_visit_date"])
    context.get_list = get_sales_visit_plan_list

def get_sales_visit_plan_list(doctype, filters, start, page_len, order_by):
    # Fetch main Sales Visit Plan documents
    sales_visit_plans = frappe.get_list(
        doctype,
        filters=filters,
        start=start,
        page_length=page_len,
        order_by=order_by,
        fields=["name", "sales_person", "planned_visit_date", "planned_visit_count"] # Add planned_visit_count
    )

    for plan in sales_visit_plans:
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

        # Fetch customer and status from the first item if available
        if items:
            first_item = frappe.get_doc("Sales Visit Plan Item", items[0][0]) # Get the full doc for customer/status
            plan.customer = first_item.customer
            plan.status = first_item.status
        else:
            plan.customer = "N/A"
            plan.status = "N/A"

    return sales_visit_plans