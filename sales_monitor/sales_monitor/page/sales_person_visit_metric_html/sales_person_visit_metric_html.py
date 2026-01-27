import frappe
from frappe import _
import re

# Import fungsi asli dari report Anda
from sales_monitor.sales_monitor.report.sales_person_visit_metric.sales_person_visit_metric import (
    get_data, get_columns
)

@frappe.whitelist()
def get_report_data(date_from=None, date_to=None, sales_person=None):
    # s_filter adalah ID dari DocType Sales Person
    s_filter = sales_person if (sales_person and sales_person != "") else None

    # Kita kirimkan employee_id jika filter dipilih, 
    # karena database menggunakan ID Employee pada kolom sales_person
    target_filter = s_filter
    if s_filter:
        emp_id = frappe.db.get_value("Sales Person", s_filter, "employee")
        if emp_id:
            target_filter = emp_id

    filters = frappe._dict({
        "from_date": date_from,
        "to_date": date_to,
        "date_from": date_from,
        "date_to": date_to,
        "sales_person": target_filter
    })

    try:
        columns = get_columns(filters)
        data = get_data(filters)
        
        return {
            "header_rows": make_header_rows(columns),
            "columns": columns, 
            "data": data or []
        }

    except Exception as e:
        frappe.log_error("Sales Metric Execution Error", frappe.get_traceback())
        return {"error": str(e)}

def make_header_rows(columns):
    header_rows = [[], []]
    # No & Sales Name Columns
    header_rows[0].append({"label": "No", "colspan": 1, "rowspan": 2})
    header_rows[1].append({"label": "No", "hidden": True})
    header_rows[0].append({"label": "Sales Name", "colspan": 1, "rowspan": 2})
    header_rows[1].append({"label": "Sales Name", "hidden": True})

    current_date = None
    for col in columns[2:]:
        label = col.get("label", "")
        match = re.search(r"(\d{2}-\d{2}-\d{4})", label)
        if match:
            dt = match.group(1)
            if dt != current_date:
                current_date = dt
                header_rows[0].append({"label": dt, "colspan": 3})
                header_rows[1].append({"label": "Sch"})
                header_rows[1].append({"label": "Visit"})
                header_rows[1].append({"label": "Order"})
        else:
            header_rows[0].append({"label": label, "colspan": 1, "rowspan": 2})
            header_rows[1].append({"label": label, "hidden": True})
    return header_rows

@frappe.whitelist()
def get_sales_persons():
    return frappe.get_all("Sales Person", filters={"is_group": 0}, fields=["name", "sales_person_name"])