import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import now_datetime

class SalesVisitPlanItem(Document):
    def autoname(self):
        # Get current year and month
        current_date = now_datetime()
        year_month = current_date.strftime("%Y%m")

        # Construct the naming series
        # The 'YYYY' in the series will make it reset yearly
        self.name = make_autoname(f"SPV.{year_month}.#####", doc=self)