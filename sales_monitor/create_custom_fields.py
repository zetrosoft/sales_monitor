import frappe

def create_custom_fields():
    custom_fields = {
        "Payroll Entry": [
            {
                "fieldname": "custom_incentive_employee_incentive",
                "label": "Employee Incentive",
                "fieldtype": "Link",
                "options": "Employee Incentive",
                "insert_after": "salary_slip_based_on_timesheet"
            }
        ],
        "Employee Incentive": [
            {
                "fieldname": "custom_incentive_payroll_entry",
                "label": "Payroll Entry",
                "fieldtype": "Link",
                "options": "Payroll Entry",
                "read_only": 1,
                "insert_after": "incentive_amount"
            }
        ],
        "Salary Slip": [
            {
                "fieldname": "custom_is_incentive_slip",
                "label": "Is Incentive Slip",
                "fieldtype": "Check",
                "read_only": 1,
                "insert_after": "payroll_entry"
            }
        ]
    }

    for dt, fields in custom_fields.items():
        for field_data in fields:
            if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": field_data["fieldname"]}):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.update(field_data)
                custom_field.dt = dt
                custom_field.insert()
                print(f"Custom Field {field_data['fieldname']} created for {dt}")
            else:
                print(f"Custom Field {field_data['fieldname']} already exists for {dt}")

if __name__ == "__main__":
    create_custom_fields()
    frappe.db.commit()
