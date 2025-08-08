import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate, now_datetime

class SalesVisitPlan(Document):
    def before_insert(self):
        if not self.naming_series:
            self.naming_series = "SPV." + now_datetime().strftime("%y%m") + ".######"
        self.name = make_autoname(self.naming_series)

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
        if not self.is_new() and self.has_field("sales_id") and self.sales_id != frappe.db.get_value("Employee", self.sales_person, "user_id"):
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
        fields=["name", "sales_person", "planned_visit_date"]
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
            fields=["customer", "status"],
            limit=1 # Just get one item to display in the list view
        )
        if items:
            plan.customer = items[0].customer
            plan.status = items[0].status
        else:
            plan.customer = "N/A"
            plan.status = "N/A"

    return sales_visit_plans