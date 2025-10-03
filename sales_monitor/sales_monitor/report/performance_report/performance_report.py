
import frappe


def execute(filters=None):
    columns = [
        {"label": "Sales Person", "fieldname": "sales_person", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Planned Visits", "fieldname": "planned_visits", "fieldtype": "Int", "width": 120},
        {"label": "Completed Visits", "fieldname": "completed_visits", "fieldtype": "Int", "width": 140},
        {"label": "Completion Rate (%)", "fieldname": "completion_rate", "fieldtype": "Percent", "width": 150}
    ]

    data = []

    sales_people = frappe.get_all("Sales Person", fields=["name"])

    for person in sales_people:
        planned_visits = frappe.db.count("Sales Visit Plan", {"sales_person": person.name})
        completed_visits = frappe.db.count("Sales Visit Plan", {"sales_person": person.name, "status": "Completed"})
        completion_rate = (completed_visits / planned_visits) * 100 if planned_visits else 0

        data.append({
            "sales_person": person.name,
            "planned_visits": planned_visits,
            "completed_visits": completed_visits,
            "completion_rate": completion_rate
        })

    return columns, data
