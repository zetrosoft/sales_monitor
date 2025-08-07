import frappe
from frappe.utils import getdate, now_datetime

@frappe.whitelist(allow_guest=True)
def get_sales_visit_plans(sales_name, date):
    # ASSUMPTION: Your Sales Visit Plan DocType is named 'Sales Visit Plan'
    # ASSUMPTION: It has fields like 'sales_person', 'visit_date', 'customer', 'address', 'status'
    # ASSUMPTION: 'customer' field is the store name

    # Convert date string to Frappe's date format if necessary
    # For simplicity, assuming date is already in a comparable format (YYYY-MM-DD)
    today_date = getdate(date) # Use getdate to ensure proper date object

    try:
        # Fetch Sales Visit Plans for the given sales_name and today's date
        # Filter out 'Selesai' status as per PWA logic
        raw_visit_plans = frappe.db.get_list(
            "Sales Visit Plan",
            filters={
                "sales_person": sales_name,
                "planned_visit_date": today_date, # Changed to planned_visit_date as per db structure
                "status": ["!=", "Selesai"] # Exclude completed plans
            },
            fields=[
                "name",
                "customer as store_name", # Using customer_name as per db structure
                "planned_location_address as address", # Using planned_location_address as per db structure
                "status",
                "planned_location_latitude as latitude", # Using planned_location_latitude as per db structure
                "planned_location_longitude as longitude", # Using planned_location_longitude as per db structure
                "planned_visit_date",
                "planned_visit_time",
                "notes",
                "sales_activity_log"
            ]
        )
        # Manually convert to list of dictionaries if not already
        visit_plans = [dict(d) for d in raw_visit_plans]
        return visit_plans
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_sales_visit_plans")
        frappe.throw(f"Failed to fetch sales visit plans: {e}")

@frappe.whitelist()
def update_sales_visit_plan_status(name, new_status, latitude=None, longitude=None, photo_url=None):
    # ASSUMPTION: Your Sales Visit Plan DocType is named 'Sales Visit Plan'
    # ASSUMPTION: It has fields like 'status', 'checkin_time', 'checkout_time', 'latitude', 'longitude', 'photo_url'
    # ASSUMPTION: You have a 'Sales Activity Log' DocType to record activities

    try:
        doc = frappe.get_doc("Sales Visit Plan", name)
        doc.status = new_status

        if new_status == "Check-in":
            doc.checkin_time = now_datetime()
            # Log activity
            frappe.get_doc({
                "doctype": "Sales Activity Log", # ASSUMPTION: DocType name
                "activity_type": "Check-in",
                "sales_visit_plan": name,
                "activity_time": now_datetime(),
                "sales_person": doc.sales_person, # ASSUMPTION: sales_person field exists
                "customer": doc.customer # ASSUMPTION: customer field exists
            }).insert(ignore_permissions=True)

        elif new_status == "Completed":
            doc.checkout_time = now_datetime()
            doc.latitude = latitude
            doc.longitude = longitude
            doc.photo_url = photo_url # This might need special handling for file uploads in Frappe

            # Log activity
            frappe.get_doc({
                "doctype": "Sales Activity Log", # ASSUMPTION: DocType name
                "activity_type": "Checkout",
                "sales_visit_plan": name,
                "activity_time": now_datetime(),
                "sales_person": doc.sales_person, # ASSUMPTION: sales_person field exists
                "customer": doc.customer, # ASSUMPTION: customer field exists
                "latitude": latitude,
                "longitude": longitude,
                "photo_url": photo_url
            }).insert(ignore_permissions=True)

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return "Success"
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in update_sales_visit_plan_status")
        frappe.throw(f"Failed to update sales visit plan status: {e}")

@frappe.whitelist()
def get_order_history(store_name):
    # ASSUMPTION: Your Sales Order DocType is named 'Sales Order'
    # ASSUMPTION: It has a field like 'customer_name' that matches store_name
    # ASSUMPTION: It has fields like 'name' (for order_id), 'transaction_date', 'grand_total'

    try:
        raw_orders = frappe.db.get_list(
            "Sales Order", # ASSUMPTION: DocType name
            filters={
                "customer_name": store_name # ASSUMPTION: field name
            },
            fields=[
                "name as order_id",
                "transaction_date as date", # ASSUMPTION: field name
                "grand_total as total" # ASSUMPTION: field name
            ],
            order_by="transaction_date desc",
            limit=5 # Limit to last 5 orders for example
        )
        # Manually convert to list of dictionaries if not already
        orders = [dict(d) for d in raw_orders]
        return orders
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_order_history")
        frappe.throw(f"Failed to fetch order history: {e}")

@frappe.whitelist()
def get_employee_id(user_id):
    try:
        employee = frappe.db.get_value("Employee", {"user_id": user_id}, "name")
        return employee
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_employee_id")
        frappe.throw(f"Failed to fetch employee ID: {e}")

@frappe.whitelist()
def get_current_user_id():
    try:
        return frappe.session.user
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_current_user_id")
        frappe.throw(f"Failed to get current user ID: {e}")