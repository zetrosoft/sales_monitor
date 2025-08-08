import frappe
from frappe.utils import getdate, now_datetime
from frappe.auth import LoginManager

@frappe.whitelist(allow_guest=True)
def pwa_login(usr, pwd):
    try:
        # Explicitly disable CSRF check for this guest-allowed login method
        frappe.request.csrf_token = frappe.request.headers.get('X-Frappe-CSRF-Token')
        login_manager = LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        user_roles = frappe.get_roles()
        employee_id = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")

        return {
            "status": "success",
            "sid": frappe.session.sid,
            "user_id": frappe.session.user,
            "full_name": frappe.session.user_full_name,
            "employee_id": employee_id,
            "roles": user_roles 
        }
    except frappe.exceptions.AuthenticationError:
        return {"status": "error", "message": "Invalid login credentials."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PWA Login Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def update_activity_from_pwa(activity_log_id, latitude, longitude, photo_url):
    """
    Updates the Sales Activity Log with data from the PWA.
    """
    try:
        activity_log = frappe.get_doc("Sales Activity Log", activity_log_id)
        
        if not activity_log.check_in_photo:
            activity_log.check_in_time = frappe.utils.now_datetime()
            activity_log.actual_location_latitude = latitude
            activity_log.actual_location_longitude = longitude
            activity_log.check_in_photo = photo_url
            
            visit_plan = frappe.get_doc("Sales Visit Plan", activity_log.sales_visit_plan)
            visit_plan.status = "Checked In"
            visit_plan.save()
        else:
            activity_log.check_out_time = frappe.utils.now_datetime()
            activity_log.check_out_photo = photo_url
            
            visit_plan = frappe.get_doc("Sales Visit Plan", activity_log.sales_visit_plan)
            visit_plan.status = "Completed"
            visit_plan.save()

        activity_log.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"status": "success", "message": f"Activity {activity_log_id} updated."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PWA Activity Update Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_sales_visit_plans(sales_name, date):
    today_date = getdate(date)
    try:
        frappe.log_error(f"get_sales_visit_plans called with sales_name={sales_name}, date={date}", "PWA Visit Plan Debug")

        parent_plan_name = frappe.db.get_value(
            "Sales Visit Plan",
            filters={"sales_person": sales_name, "planned_visit_date": today_date},
            fieldname="name"
        )

        if not parent_plan_name:
            frappe.log_error(f"No parent plan found for sales_name={sales_name}, date={date}", "PWA Visit Plan Debug")
            return [] # No plan for today

        frappe.log_error(f"Parent plan found: {parent_plan_name}", "PWA Visit Plan Debug")

        visit_items = frappe.db.get_list(
            "Sales Visit Plan Item",
            filters={
                "parent": parent_plan_name,
                "status": ["!=", "Selesai"]
            },
            fields=[
                "name",
                "customer as store_name",
                "address",
                "status",
                "visit_time as planned_visit_time",
                "notes",
                "sales_activity_log"
            ],
            ignore_permissions=True
        )
        
        # Post-process to handle null status
        processed_items = []
        for item in visit_items:
            processed_item = dict(item) # Convert Row object to dict
            if processed_item.get('status') is None or processed_item.get('status') == '':
                processed_item['status'] = 'Planned' # Default to 'Planned' if status is null or empty
            processed_items.append(processed_item)

        return processed_items

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_sales_visit_plans")
        frappe.throw(f"Failed to fetch sales visit plans: {e}")

@frappe.whitelist()
def update_sales_visit_plan_status(name, new_status, latitude=None, longitude=None, photo_url=None):
    try:
        # 'name' is the name of the Sales Visit Plan Item document
        doc = frappe.get_doc("Sales Visit Plan Item", name)
        doc.status = new_status

        # Get the parent document to access sales_person
        parent_doc = frappe.get_doc("Sales Visit Plan", doc.parent)

        if new_status == "Checked In":
            # Log activity
            frappe.get_doc({
                "doctype": "Sales Activity Log",
                "activity_type": "Check-in",
                "sales_visit_plan_item": name, # Link to the child doc
                "activity_time": now_datetime(),
                "sales_person": parent_doc.sales_person,
                "customer": doc.customer
            }).insert(ignore_permissions=True)

        elif new_status == "Completed":
            # Log activity
            frappe.get_doc({
                "doctype": "Sales Activity Log",
                "activity_type": "Checkout",
                "sales_visit_plan_item": name, # Link to the child doc
                "activity_time": now_datetime(),
                "sales_person": parent_doc.sales_person,
                "customer": doc.customer,
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
    try:
        raw_orders = frappe.db.get_list(
            "Sales Order",
            filters={
                "customer_name": store_name
            },
            fields=[
                "name as order_id",
                "transaction_date as date",
                "grand_total as total"
            ],
            order_by="transaction_date desc",
            limit=5
        )
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

@frappe.whitelist(allow_guest=True)
def get_current_user_id():
    try:
        return frappe.session.user
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_current_user_id")
        frappe.throw(f"Failed to get current user ID: {e}")

@frappe.whitelist(allow_guest=True)
def get_sales_activity_history(sales_person, from_date=None, to_date=None, customer=None):
    try:
        filters = {
            "sales_person": sales_person
        }

        if from_date:
            from_date = getdate(from_date)
        if to_date:
            to_date = getdate(to_date)

        if from_date and to_date:
            filters["activity_time"] = ["between", (from_date, to_date)]
        elif from_date:
            filters["activity_time"] = [">=", from_date]
        elif to_date:
            filters["activity_time"] = ["<=", to_date]

        if customer:
            filters["customer_name"] = customer

        raw_activities = frappe.db.get_list(
            "Sales Activity Log",
            filters=filters,
            fields=[
                "activity_time",
                "customer_name",
                "activity_type",
                "check_in_time",
                "check_out_time",
            ],
            order_by="activity_time desc"
        )

        activities = []
        for d in raw_activities:
            activity = dict(d)
            formatted_activity = {
                "Date": frappe.utils.formatdate(activity.get("activity_time"), "YYYY-MM-DD") if activity.get("activity_time") else None,
                "Customer": activity.get("customer_name"),
                "Checkin": frappe.utils.format_time(activity.get("check_in_time")) if activity.get("check_in_time") else None,
                "Checkout": frappe.utils.format_time(activity.get("check_out_time")) if activity.get("check_out_time") else None,
                "Duration": 0,
                "Status": activity.get("activity_type")
            }

            if activity.get("check_in_time") and activity.get("check_out_time"):
                checkin = frappe.utils.get_datetime(activity["check_in_time"])
                checkout = frappe.utils.get_datetime(activity["check_out_time"])
                duration_seconds = (checkout - checkin).total_seconds()
                formatted_activity["Duration"] = round(duration_seconds / 60)

            activities.append(formatted_activity)

        return activities
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_sales_activity_history")
        frappe.throw(f"Failed to fetch sales activity history: {e}")