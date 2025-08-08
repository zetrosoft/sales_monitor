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
        # The status change from Draft to Planned is handled by the JS side
        # when the "Submit Plan" button is clicked, which calls frm.save('Submit').
        # No need for self.save() here as it's already part of the save cycle.
        pass

    def on_cancel(self):
        # Allow cancellation only if status is not 'Completed'
        if self.status == "Completed":
            frappe.throw("Cannot cancel a Completed Sales Visit Plan.")
        self.status = "Cancelled"
        # No need for self.save() here as it's already part of the save cycle.

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
        # This check should be done carefully to avoid blocking legitimate updates
        # For now, assuming it's set once and shouldn't change.
        # If sales_id is already set and sales_person changes, it should update sales_id
        # but not throw an error if the sales_id itself is being changed directly.
        # The current logic prevents any change to sales_id if it's already set and not new.
        # This might be too restrictive. Re-evaluating based on "read_only: 1" in JSON.
        # If read_only in JSON, then the JS should prevent direct user input.
        # The Python validation should primarily ensure it's set correctly initially.
        pass # Removed the restrictive sales_id validation for now, relying on read_only in JSON