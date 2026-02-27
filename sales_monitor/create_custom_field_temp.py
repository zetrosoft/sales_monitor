import frappe

def create_sales_incentive_payment_ref_custom_field():
    doctype_name = "Employee Incentive"
    fieldname = "sales_incentive_payment_ref"
    label = "Sales Incentive Payment Ref"

    if frappe.db.exists("Custom Field", {"dt_name": doctype_name, "fieldname": fieldname}):
        frappe.msgprint(f"Custom Field '{label}' ({fieldname}) already exists for DocType '{doctype_name}'.")
        return

    try:
        cf = frappe.get_doc({
            "doctype": "Custom Field",
            "dt_name": doctype_name,
            "fieldname": fieldname,
            "label": label,
            "fieldtype": "Link",
            "options": "Sales Incentive Payment",
            "read_only": 1,
            "hidden": 0,
            "insert_after": "employee", # Sesuaikan jika ingin posisi berbeda
            "allow_on_submit": 0,
            "bold": 0,
            "in_global_search": 0,
            "in_list_view": 0,
            "in_standard_filter": 0,
            "in_preview": 0,
            "no_copy": 0,
            "permlevel": 0,
            "print_hide": 0,
            "reqd": 0,
            "search_index": 0,
        })
        cf.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.msgprint(f"Custom Field '{label}' ({fieldname}) created successfully for DocType '{doctype_name}'.")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating Custom Field for Employee Incentive")
        frappe.msgprint(f"Failed to create Custom Field: {e}")

if __name__ == "__main__":
    create_sales_incentive_payment_ref_custom_field()
