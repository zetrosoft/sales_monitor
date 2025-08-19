import frappe
from frappe.utils import getdate, now_datetime

@frappe.whitelist()
def get_sales_activity_monitoring_data(sales_person=None, customer=None, from_date=None, to_date=None):
    # Temporarily return dummy data for debugging frontend
    return [
        {
            "name": "SAM-00001",
            "sales_name": "John Doe",
            "customer": "Acme Corp",
            "plan_date_time": "2025-08-19 10:00:00",
            "duration_visit": 60,
            "map_link": "https://maps.google.com/?q=34.0522,-118.2437", # Example coordinates for Los Angeles
            "image_link": "https://via.placeholder.com/30", # Placeholder image
            "status": "Completed",
            "checkin_raw": "2025-08-19 09:55:00",
            "checkout_raw": "2025-08-19 10:55:00"
        },
        {
            "name": "SAM-00002",
            "sales_name": "Jane Smith",
            "customer": "Globex Inc.",
            "plan_date_time": "2025-08-19 14:30:00",
            "duration_visit": 30,
            "map_link": "https://maps.google.com/?q=40.7128,-74.0060", # Example coordinates for New York
            "image_link": "https://via.placeholder.com/30",
            "status": "Planned",
            "checkin_raw": None,
            "checkout_raw": None
        }
    ]

@frappe.whitelist()
def get_customer_visit_info(customer_name):
    # Dummy data for customer visit info
    if customer_name == "Acme Corp":
        return {
            "customer_name": "Acme Corp",
            "address": "123 Main St, Anytown, USA",
            "visit_count_last_year": 10
        }
    elif customer_name == "Globex Inc.":
        return {
            "customer_name": "Globex Inc.",
            "address": "456 Oak Ave, Otherville, USA",
            "visit_count_last_year": 5
        }
    return None