# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {
            "label": _("ID"),
            "fieldname": "name",
            "fieldtype": "Data",
            
            "hidden": 1
        },
        {
            "label": _("Sales Name"),
            "fieldname": "sales_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Plan Date"),
            "fieldname": "plan_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Visit Date"),
            "fieldname": "visit_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Duration"),
            "fieldname": "duration",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Photo"),
            "fieldname": "photo",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Map"),
            "fieldname": "map_location",
            "fieldtype": "Data",
            "width": 70
        },
        # Hidden fields for frontend use
        {
            "fieldname": "customer_address",
            "hidden": 1
        },
        {
            "fieldname": "latitude",
            "hidden": 1
        },
        {
            "fieldname": "longitude",
            "hidden": 1
        }
    ]

def get_data(filters):
    sql = """
        SELECT
            sam.name,
            emp.employee_name AS sales_name,
            cus.customer_name AS customer,
            sam.plan_date,
            sam.visit_date,
            TIMEDIFF(sam.check_out_time, sam.check_in_time) AS duration,
            sam.photo,
            cus.custom_address AS customer_address,
            sam.latitude,
            sam.longitude,
            sam.map_link AS map_location
        FROM
            `tabSales Activity Monitoring` AS sam
        LEFT JOIN
            `tabEmployee` AS emp ON sam.sales_person = emp.name
        LEFT JOIN
            `tabCustomer` AS cus ON sam.customer = cus.name
        WHERE
            1=1
    """

    sql_filters = []
    if filters.get("sales_person"):
        sql_filters.append(f"sam.sales_person = '{filters['sales_person']}'")
    
    if filters.get("customer"):
        sql_filters.append(f"sam.customer = '{filters['customer']}'")

    if filters.get("date_range"):
        start_date, end_date = filters["date_range"]
        sql_filters.append(f"sam.plan_date BETWEEN '{start_date}' AND '{end_date}'")

    if sql_filters:
        sql += " AND " + " AND ".join(sql_filters)

    return frappe.db.sql(sql, as_dict=True)

