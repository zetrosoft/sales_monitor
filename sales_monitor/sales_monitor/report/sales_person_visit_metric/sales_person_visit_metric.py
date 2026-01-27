# Copyright (c) 2026, Siumang and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import timedelta

def execute(filters=None):
    columns, data = [], []
    
    columns = get_columns(filters)
    data = get_data(filters)
    
    return columns, data

def get_columns(filters):
    columns = [
        {
            "label": _("No"),
            "fieldname": "no",
            "fieldtype": "Data",
            "width": 50
        },
        {
            "label": _("Sales Name"),
            "fieldname": "sales_person_name",
            "fieldtype": "Link",
            "options": "Sales Person",
            "width": 200
        }
    ]

    start_date = frappe.utils.get_datetime(filters.get("date_from")).date()
    end_date = frappe.utils.get_datetime(filters.get("date_to")).date()
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        # Header column for the date
        columns.append({
            "label": current_date.strftime("%d-%m-%Y"),
            "fieldname": date_str,
            "fieldtype": "Data",
            "width": 210,
        })
        current_date += timedelta(days=1)
        
    return columns

def get_data(filters):
    # Get date range
    start_date = frappe.utils.get_datetime(filters.get("date_from")).date()
    end_date = frappe.utils.get_datetime(filters.get("date_to")).date()

    # Determine sales_persons to report on and their corresponding Employee and User IDs
    sales_data_map = {} # Maps Sales Person name to {employee_name, user_id}

    if filters.get("sales_person"):
        # If a specific Sales Person is selected, fetch their Employee and User ID
        sales_person_name_from_filter = filters["sales_person"]
        # Assuming Sales Person DocType has a field 'employee' that links to Employee
        employee_name = frappe.db.get_value("Sales Person", sales_person_name_from_filter, "employee")
        user_id = frappe.db.get_value("Employee", employee_name, "user_id") if employee_name else None
        
        if employee_name:
            sales_data_map[sales_person_name_from_filter] = {
                "sales_person_name": frappe.db.get_value("Sales Person", sales_person_name_from_filter, "sales_person_name"),
                "employee_name": employee_name,
                "user_id": user_id
            }
    else:
        # Fetch all Sales Persons and their associated Employee and User IDs
        all_sales_persons = frappe.get_all("Sales Person", fields=["name", "sales_person_name", "employee"]) # Added 'employee' field to fetch
        for sp_doc in all_sales_persons:
            employee_name = sp_doc.get("employee")
            user_id = frappe.db.get_value("Employee", employee_name, "user_id") if employee_name else None
            if employee_name:
                sales_data_map[sp_doc.name] = {
                    "sales_person_name": sp_doc.sales_person_name,
                    "employee_name": employee_name,
                    "user_id": user_id
                }
    
        # Get data from DocTypes
        all_schedules = get_schedules(filters)
        all_visits = get_visits(filters)
        all_orders = get_orders(filters)
    
        processed_data = {}
    
        for sp_name, sp_map_data in sales_data_map.items():
            employee_name = sp_map_data["employee_name"]
            employee_user_id = sp_map_data["user_id"]
            display_name = sp_map_data["sales_person_name"]
    
            processed_data[employee_name] = {"sales_person_name": display_name}
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                
                schedule_count = all_schedules.get((employee_name, date_str), 0)
                visit_count = all_visits.get((employee_name, date_str), 0)
                order_count = all_orders.get((employee_user_id, date_str), 0) # Orders are linked by user_id/owner
                
                display_text = f"Sch: {schedule_count} | Visit: {visit_count} | Order: {order_count}"
    
                processed_data[employee_name][date_str] = display_text
                current_date += timedelta(days=1)
                
        # Format for report
        report_data = []
        for i, (emp_name, values) in enumerate(processed_data.items()):
            row = {
                "no": i + 1,
                "sales_person_name": values.pop("sales_person_name"), # Get and remove employee_name from values
            }
            row.update(values)
            report_data.append(row)
            
        return report_data


def get_schedules(filters, employee_name=None):
    """Fetch Sales Visit Plan data."""
    conditions = {
        "planned_visit_date": ["between", (filters.get("date_from"), filters.get("date_to"))]
    }
    if employee_name:
        conditions["sales_person"] = employee_name

    data = frappe.get_all("Sales Visit Plan",
        filters=conditions,
        fields=["sales_person", "planned_visit_date"],
        group_by="sales_person, planned_visit_date",
        as_list=True
    )
    # Count occurrences
    counts = {}
    for sales_person, schedule_date in data:
        date_str = schedule_date.strftime("%Y-%m-%d")
        key = (sales_person, date_str)
        counts[key] = counts.get(key, 0) + 1
    return counts

def get_visits(filters, employee_name=None):
    """Fetch Sales Activity Monitoring data."""
    conditions = {
        "checkin_time": ["between", (filters.get("date_from"), filters.get("date_to"))]
    }
    if employee_name:
        conditions["sales_person"] = employee_name
    
    data = frappe.get_all("Sales Activity Monitoring",
        filters=conditions,
        fields=["sales_person", "checkin_time"],
        group_by="sales_person, checkin_time",
        as_list=True
    )
    counts = {}
    for sales_person, visit_date in data:
        date_str = visit_date.strftime("%Y-%m-%d")
        key = (sales_person, date_str)
        counts[key] = counts.get(key, 0) + 1
    return counts

def get_orders(filters, user_id=None):
    """Fetch Sales Order data."""
    conditions = {
        "transaction_date": ["between", (filters.get("date_from"), filters.get("date_to"))],
        "status": ["!=", "Cancelled"]
    }
    if user_id:
        conditions["owner"] = user_id
    
    data = frappe.get_all("Sales Order",
        filters=conditions,
        fields=["owner", "transaction_date"],
        group_by="owner, transaction_date",
        as_list=True
    )
    counts = {}
    for sales_person, order_date in data:
        date_str = order_date.strftime("%Y-%m-%d")
        key = (sales_person, date_str)
        counts[key] = counts.get(key, 0) + 1
    return counts

