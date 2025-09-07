from __future__ import unicode_literals
import frappe
from sales_monitor.api import get_sales_activity_monitoring_data

def execute(filters=None):
    columns = [
        {"fieldname": "name", "label": "ID", "fieldtype": "Data", "width": 100},
        {"fieldname": "sales_name", "label": "Sales Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"fieldname": "plan_date_time", "label": "Plan Date Time", "fieldtype": "Datetime", "width": 180},
        {"fieldname": "duration_visit", "label": "Duration (mins)", "fieldtype": "Float", "width": 120},
        {"fieldname": "map_link", "label": "Map Link", "fieldtype": "Data", "width": 100},
        {"fieldname": "image_link", "label": "Image Link", "fieldtype": "Data", "width": 100},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
        {"fieldname": "checkin_raw", "label": "Checkin Raw", "fieldtype": "Datetime", "hidden": 1},
        {"fieldname": "checkout_raw", "label": "Checkout Raw", "fieldtype": "Datetime", "hidden": 1},
    ]

    # Call the existing API method to get data
    data = get_sales_activity_monitoring_data(
        sales_person=filters.get("sales_person"),
        customer=filters.get("customer"),
        from_date=filters.get("from_date"),
        to_date=filters.get("to_date")
    )

    # Convert list of dicts to list of lists for report view
    report_data = []
    for row in data:
        report_data.append([
            row.get("name"),
            row.get("sales_name"),
            row.get("customer"),
            row.get("plan_date_time"),
            row.get("duration_visit"),
            row.get("map_link"),
            row.get("image_link"),
            row.get("status"),
            row.get("checkin_raw"),
            row.get("checkout_raw")
        ])

    return columns, report_data
