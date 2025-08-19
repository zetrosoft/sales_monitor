# Copyright (c) 2024, Gemini and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime
from sales_monitor.api import get_sales_activity_monitoring_data

class SalesActivityMonitoring(Document):
    def get_list(self, filters, start, page_len, order_by):
        print(f"DEBUG: get_list called with filters: {filters}") # Added print statement
        sales_person = filters.get("sales_person")
        customer = filters.get("customer")
        from_date = filters.get("from_date")
        to_date = filters.get("to_date")

        data = get_sales_activity_monitoring_data(
            sales_person=sales_person,
            customer=customer,
            from_date=from_date,
            to_date=to_date
        )
        print(f"DEBUG: Data from get_sales_activity_monitoring_data: {data}") # Added print statement
        return data

    def get_count(self, filters):
        # For simplicity, return the count of the list data
        data = self.get_list(filters, None, None, None)
        return len(data)

    def get_stats(self, filters):
        # Implement as needed, or return empty dict if not used
        return {}
