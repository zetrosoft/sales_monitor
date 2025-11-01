import frappe
from frappe.utils import getdate

@frappe.whitelist()
def get_todays_visits(sales_person, visit_date):
    if not sales_person or not visit_date:
        return []

    try:
        date_obj = getdate(visit_date)
    except Exception:
        return [] # Return empty if date is invalid

    results = []
    visited_customers = set()

    # 1. Get completed visits from Sales Activity Monitoring for the given date
    completed_visits = frappe.get_all(
        "Sales Activity Monitoring",
        filters={
            "sales_person": sales_person,
            "checkin_time": ["between", (f"{visit_date} 00:00:00", f"{visit_date} 23:59:59")]
        },
        fields=["customer", "latitude", "longitude", "image_link"]
    )

    for visit in completed_visits:
        if visit.latitude and visit.longitude:
            results.append({
                "lat": float(visit.latitude),
                "lng": float(visit.longitude),
                "customer": visit.customer,
                "status": "Visited",
                "photo": visit.image_link or None
            })
            visited_customers.add(visit.customer)

    # 2. Get planned visits from submitted Sales Visit Plans for the same date
    #    and filter out customers who have already been visited.
    planned_items = frappe.get_all(
        "Sales Visit Plan Item",
        filters={
            "parenttype": "Sales Visit Plan",
            "parent.docstatus": 1,  # Only from submitted plans
            "parent.sales_person": sales_person,
            "parent.planned_visit_date": date_obj,
            "status": "Planned"
        },
        # Fetch lat/lng from the linked Customer document
        fields=["name", "customer", "`tabCustomer`.custom_latitude as lat", "`tabCustomer`.custom_longitude as lng"],
        # Join with Customer table to get coordinates
        joins=["left join `tabCustomer` on `tabSales Visit Plan Item`.customer = `tabCustomer`.name"]
    )

    for item in planned_items:
        if item.customer not in visited_customers and item.lat and item.lng:
            results.append({
                "lat": float(item.lat),
                "lng": float(item.lng),
                "customer": item.customer,
                "status": "Planned",
                "photo": None
            })

    return results

@frappe.whitelist()
def get_sales_team_employees(doctype, txt, searchfield, start, page_len, filters):
    """
    Returns a list of Employees who are linked to an active Sales Person for use in a link field query.
    """
    sales_person_employees = frappe.get_all(
        "Sales Person",
        filters={"enabled": 1},
        fields=["employee"],
        pluck="employee",
        distinct=True
    )

    employee_filters = [
        ["name", "in", sales_person_employees],
        [searchfield, "like", f"%{txt}%"],
    ]

    return frappe.get_list(
        doctype,
        filters=employee_filters,
        fields=["name", "employee_name"],
        as_list=True,
        page_length=page_len,
        start=start,
        order_by="name"
    )
