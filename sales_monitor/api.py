import frappe
from frappe.utils import getdate, now_datetime, get_first_day, get_last_day, get_datetime, add_days, get_first_day_of_week, get_last_day_of_week
from frappe.auth import LoginManager

@frappe.whitelist(allow_guest=True)
def pwa_login(usr, pwd):
    try:
        # Force CSRF token to be valid for this request
        # frappe.request.csrf_token = frappe.request.headers.get('X-Frappe-CSRF-Token') or '' # Nonaktifkan untuk login awal PWA
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


@frappe.whitelist(allow_guest=True)
def get_sales_visit_plans(date=None, limit_start=0, limit_page_length=5):
    try:
        sales_person = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not sales_person:
            frappe.throw("Employee ID not found for current user.")

        parent_plans = frappe.db.get_all(
            "Sales Visit Plan",
            filters={"sales_person": sales_person},
            fields=["name", "planned_visit_date", "docstatus"]  # Fetch docstatus
        )

        if not parent_plans:
            return []

        parent_plan_names = [p["name"] for p in parent_plans]
        plan_dates = {p["name"]: p["planned_visit_date"] for p in parent_plans}
        plan_statuses = {p["name"]: p["docstatus"] for p in parent_plans}  # Store docstatus

        visit_items = frappe.db.get_list(
            "Sales Visit Plan Item",
            filters={
                "parent": ["in", parent_plan_names],
                "status": ["not in", ["Completed", "Cancelled"]]
            },
            fields=[
                "name", "parent", "customer as store_name", "address",
                "status", "visit_time", "notes"
            ],
            ignore_permissions=True
        )

        visit_item_names = [item['name'] for item in visit_items]
        
        activity_docs = frappe.db.get_all(
            "Sales Activity Monitoring",
            filters={"sales_visit_plan_item": ["in", visit_item_names]},
            fields=["sales_visit_plan_item", "checkin_time", "checkout_time"]
        )

        activity_times = {}
        for doc in activity_docs:
            activity_times[doc.sales_visit_plan_item] = {
                "checkin_time": doc.checkin_time,
                "checkout_time": doc.checkout_time
            }

        processed_items = []
        for item in visit_items:
            processed_item = dict(item)
            if not processed_item.get('status'):
                processed_item['status'] = 'Planned'

            parent_name = processed_item.get("parent")
            planned_date = plan_dates.get(parent_name)
            visit_time = processed_item.get('visit_time')
            
            # Add parent docstatus to the item
            processed_item['parent_docstatus'] = plan_statuses.get(parent_name, 0) # Default to Draft

            if planned_date and visit_time:
                processed_item['planned_visit_time'] = f"{frappe.utils.format_date(planned_date, 'dd-MM-yyyy')} {frappe.utils.format_time(visit_time, 'HH:mm')}"
            elif planned_date:
                processed_item['planned_visit_time'] = frappe.utils.format_date(planned_date, 'dd-MM-yyyy')
            else:
                processed_item['planned_visit_time'] = visit_time or ''

            activities = activity_times.get(item.name, {})
            checkin_time = activities.get('checkin_time')
            checkout_time = activities.get('checkout_time')

            if checkin_time:
                processed_item['checkin_time'] = frappe.utils.format_datetime(checkin_time, 'dd/MM/yy HH:mm:ss')
            if checkout_time:
                processed_item['checkout_time'] = frappe.utils.format_datetime(checkout_time, 'dd/MM/yy HH:mm:ss')

            processed_item['sort_key_date'] = planned_date or frappe.utils.getdate('1900-01-01')
            processed_item['sort_key_time'] = visit_time or '00:00:00'

            if 'visit_time' in processed_item:
                del processed_item['visit_time']
            

            processed_items.append(processed_item)

        processed_items.sort(key=lambda x: (STATUS_ORDER.get(x.get('status', 'Draft'), 99), x['sort_key_date'], x['sort_key_time']))

        limit_start = int(limit_start)
        limit_page_length = int(limit_page_length)
        paginated_items = processed_items[limit_start : limit_start + limit_page_length]

        for item in paginated_items:
            del item['sort_key_date']
            del item['sort_key_time']

        return paginated_items

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_sales_visit_plans")
        frappe.throw(f"Failed to fetch sales visit plans: {e}")

STATUS_ORDER = {
    "Planned": 0,
    "Checked In":1,
    "Completed": 2,
    "Canceled": 3,
    "Draft": 4,
}



import frappe
from frappe.utils.file_manager import save_file # Import save_file

@frappe.whitelist()
def submit_visit_update(name, new_status, latitude=None, longitude=None, photo=None):
    try:
        doc = frappe.get_doc("Sales Visit Plan Item", name)
        parent_doc = frappe.get_doc("Sales Visit Plan", doc.parent)

        photo_url = None
        if photo: # Check if photo is provided as an argument
            file_doc = save_file(photo.filename, photo.stream.read(), "Sales Activity Monitoring", name)
            photo_url = file_doc.file_url
        elif frappe.request.files: # Fallback for file uploads via request.files
            files = frappe.request.files.getlist("photo")
            if files:
                file_doc = save_file(files[0].filename, files[0].stream.read(), "Sales Activity Monitoring", name)
                photo_url = file_doc.file_url

        if new_status == "Checked In":
            doc.status = "Checked In"
            
            activity = frappe.new_doc("Sales Activity Monitoring")
            activity.sales_person = parent_doc.sales_person
            activity.employee_name = frappe.db.get_value("Employee", parent_doc.sales_person, "employee_name")
            activity.customer = doc.customer
            activity.sales_visit_plan_item = name
            activity.checkin_time = now_datetime()
            activity.status = "Checked In"
            activity.notes = doc.notes
            if parent_doc.planned_visit_date and doc.visit_time:
                activity.plan_date_time = f"{parent_doc.planned_visit_date} {doc.visit_time}"

            if latitude and longitude:
                activity.map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                activity.latitude = latitude
                activity.longitude = longitude
            
            if photo_url: # Save image_link on check-in if photo is provided
                activity.image_link = photo_url

            activity.insert(ignore_permissions=True)

        elif new_status == "Completed":
            doc.status = "Completed"

            activity_name = frappe.db.get_value("Sales Activity Monitoring", {"sales_visit_plan_item": name}, "name")
            if activity_name:
                activity = frappe.get_doc("Sales Activity Monitoring", activity_name)
                activity.checkout_time = now_datetime()
                activity.status = "Completed"
                
                if photo_url: # Update image_link on checkout if photo is provided
                    activity.image_link = photo_url
                
                if latitude and longitude: # Update map_link and lat/lon on checkout if provided
                    activity.map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                    activity.latitude = latitude
                    activity.longitude = longitude

                if activity.checkin_time and activity.checkout_time:
                    checkin = get_datetime(activity.checkin_time)
                    checkout = get_datetime(activity.checkout_time)
                    duration_seconds = (checkout - checkin).total_seconds()
                    activity.duration = round(duration_seconds / 60)

                activity.save(ignore_permissions=True)
            else:
                frappe.log_error("Could not find matching Sales Activity Monitoring doc for checkout.", f"Sales Visit Plan Item: {name}")


        doc.flags.ignore_validate_update_after_submit = True
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": "Visit plan updated successfully."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in submit_visit_update")
        return {"status": "error", "message": str(e)}

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
def get_sales_activity_history(from_date=None, to_date=None, customer=None):
    try:
        sales_person = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not sales_person:
            frappe.throw("Employee ID not found for current user.")

        filters = {
            "sales_person": sales_person
        }

        if from_date:
            from_date = getdate(from_date)
        if to_date:
            to_date = getdate(to_date)

        if from_date and to_date:
            filters["checkin_time"] = ["between", (from_date, to_date)]
        elif from_date:
            filters["checkin_time"] = [">=", from_date]
        elif to_date:
            filters["checkin_time"] = ["<=", to_date]

        if customer:
            filters["customer"] = ["like", f"%{customer}%"]

        raw_activities = frappe.db.get_list(
            "Sales Activity Monitoring",
            filters=filters,
            fields=[
                "checkin_time",
                "checkout_time",
                "customer",
                "duration",
                "status"
            ],
            order_by="checkin_time desc"
        )

        activities = []
        for d in raw_activities:
            activity = dict(d)
            formatted_activity = {
                "Date": frappe.utils.format_date(activity.get("checkin_time")) if activity.get("checkin_time") else None,
                "Customer": activity.get("customer"),
                "Checkin": frappe.utils.format_time(activity.get("checkin_time")) if activity.get("checkin_time") else None,
                "Checkout": frappe.utils.format_time(activity.get("checkout_time")) if activity.get("checkout_time") else None,
                "Duration": activity.get("duration", 0),
                "Status": activity.get("status")
            }
            activities.append(formatted_activity)

        return activities
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_sales_activity_history")
        frappe.throw(f"Failed to fetch sales activity history: {e}")

@frappe.whitelist(allow_guest=True)
def get_dashboard_data():
    sales_person = None
    today_date = frappe.utils.today()
    try:
        # Get the sales person for the current user
        sales_person = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not sales_person:
            return {"status": "error", "message": "Employee not found for the current user."}

        # Get all parent Sales Visit Plan names for today
        today_parent_plans = frappe.db.get_list(
            "Sales Visit Plan",
            filters={"sales_person": sales_person, "planned_visit_date": today_date},
            fields=["name"]
        )
        parent_plan_name_list = [p.name for p in today_parent_plans] if today_parent_plans else []

        # Get all parent Sales Visit Plan names for the sales person (all dates)
        all_parent_plans = frappe.db.get_list(
            "Sales Visit Plan",
            filters={"sales_person": sales_person},
            fields=["name"]
        )
        parent_plan_all_names = [p.name for p in all_parent_plans] if all_parent_plans else []

        total_visits = 0
        completed_visits = 0
        pending_visits = 0 # Inisialisasi

        if parent_plan_name_list:
            # Get total visits for today (Draft, NULL, or Planned for today's plan)
            total_visits = frappe.db.count(
                "Sales Visit Plan Item",
                filters=[
                    ["parent", "in", parent_plan_name_list],
                    ["status", "in", ["", " ", "Draft", "Planned"]]
                ]
            )
        
        if parent_plan_all_names:
            # Get completed visits (all completed for this sales person across all plans)
            completed_visits = frappe.db.count(
                "Sales Visit Plan Item",
                filters={"parent": ["in", parent_plan_all_names], "status": "Completed"}
            )
            # Get pending visits (Outstanding Visit) (Draft, NULL, or Planned for this sales person across all plans)
            pending_visits = frappe.db.count(
                "Sales Visit Plan Item",
                filters=[
                    ["parent", "in", parent_plan_all_names],
                    ["status", "in", ["", " ", "Draft", "Planned"]]
                ]
            )


        # Calculate Achievement Percentage (Pencapaian)
        achievement_percentage = 0
        if total_visits > 0:
            achievement_percentage = (completed_visits / total_visits) * 100

        return {
            "status": "success",
            "total_visits_today": total_visits,
            "completed_visits_today": completed_visits,
            "pending_visits": pending_visits,
            # "total_sales_month": total_sales_month,
            # "total_outstanding_sales": total_outstanding_sales,
            "achievement_percentage": achievement_percentage,
            "test":parent_plan_all_names # Changed from parent_plan_all
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error in get_dashboard_data for {sales_person} on {today_date}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_weekly_visit_sales_comparison_data():
    try:
        sales_person = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not sales_person:
            return {"status": "error", "message": "Employee not found for the current user."}

        today = get_datetime(frappe.utils.today())
        
        weekly_data = {}

        for i in range(8): # Last 8 weeks
            week_start = get_first_day_of_week(add_days(today, -7 * i))
            week_end = get_last_day_of_week(add_days(today, -7 * i))
            week_label = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"

            # Get total visits for the week
            visits_in_week = 0
            plan_in_week = 0
            frappe.log_error(f"get_weekly_visit_sales_comparison_data: Querying Sales Visit Plan for sales_person: {sales_person}, week: {week_label}", "Sales Person Debug")
            parent_plans_in_week = frappe.db.get_list(
                "Sales Visit Plan",
                filters={
                    "sales_person": sales_person,
                    "planned_visit_date": ["between", [week_start, week_end]],
                    "docstatus": 1  # Only submitted plans
                },
                fields=["name"]
            )
            for plan in parent_plans_in_week:
                frappe.log_error(f"get_weekly_visit_sales_comparison_data: Querying Sales Visit Plan Item for parent: {plan.name}", "Sales Person Debug")
                visits_in_week += frappe.db.count(
                    "Sales Visit Plan Item",
                    filters={"parent": plan.name, "status": "Completed"}  # Exclude completed items
                )
            # plan visit
            for plan in parent_plans_in_week:
                frappe.log_error(f"get_weekly_visit_sales_comparison_data: Querying Sales Visit Plan Item for parent: {plan.name}", "Sales Person Debug")
                plan_in_week += frappe.db.count(
                    "Sales Visit Plan Item",
                    filters={"parent": plan.name}#, "status":["not in",["Checked In","Completed"]]}  # Exclude completed items
                )
            # Get total sales for the week
            # frappe.log_error(f"get_weekly_visit_sales_comparison_data: Querying Sales Order for sales_person: {sales_person}, week: {week_label}", "Sales Person Debug")
            # sales_in_week = frappe.db.get_value(
            #     "Sales Order",
            #     filters={
            #         "sales_person": sales_person,
            #         "transaction_date": ["between", [week_start, week_end]],
            #         "docstatus": 1 # Only submitted orders
            #     },
            #     fieldname="SUM(grand_total)"
            # ) or 0
            sales_in_week = 0
            weekly_data[week_label] = {
                "plan" : plan_in_week,
                "visits": visits_in_week,
                "sales": sales_in_week
            }
        
        # Format data for chart (e.g., labels, datasets)
        labels = list(weekly_data.keys())
        visits_data = [weekly_data[label]["visits"] for label in labels]
        sales_data = [weekly_data[label]["sales"] for label in labels]
        plan_data = [weekly_data[label]["plan"] for label in labels]
        return {
            "status": "success",
            "labels": labels,
            "datasets": [
                {"label":"Plan","data":plan_data},
                {"label": "Visits", "data": visits_data},
                #{"label": "Sales", "data": sales_data}
            ]
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_weekly_visit_sales_comparison_data")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_weekly_customer_order_data():
    try:
        sales_person = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not sales_person:
            return {"status": "error", "message": "Employee not found for the current user."}

        today = get_datetime(frappe.utils.today())
        
        customer_weekly_orders = {}

        for i in range(8): # Last 8 weeks
            week_start = get_first_day_of_week(add_days(today, -7 * i))
            week_end = get_last_day_of_week(add_days(today, -7 * i))
            week_label = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"

            frappe.log_error(f"get_weekly_customer_order_data: Querying Sales Order for sales_person: {sales_person}, week: {week_label}", "Sales Person Debug")
            orders_in_week = frappe.db.get_list(
                "Sales Order",
                filters={
                    "sales_person": sales_person,
                    "transaction_date": ["between", [week_start, week_end]],
                    "docstatus": 1 # Only submitted orders
                },
                fields=["customer_name", "grand_total"]
            )

            for order in orders_in_week:
                customer_name = order.customer_name
                grand_total = order.grand_total

                if week_label not in customer_weekly_orders:
                    customer_weekly_orders[week_label] = {}
                
                if customer_name not in customer_weekly_orders[week_label]:
                    customer_weekly_orders[week_label][customer_name] = 0
                
                customer_weekly_orders[week_label][customer_name] += grand_total
        
        # Format data for table grid
        formatted_data = []
        for week_label, customers_data in customer_weekly_orders.items():
            row = {"week": week_label}
            for customer, total_sales in customers_data.items():
                row[customer] = total_sales
            formatted_data.append(row)

        return {"status": "success", "data": formatted_data}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_weekly_customer_order_data")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_sales_activity_monitoring_data(sales_person=None, customer=None, from_date=None, to_date=None):
    try:
        filters = {}

        if sales_person:
            filters["sales_person"] = sales_person
        else:
            # If no sales_person is provided, default to current user's sales_person
            current_sales_person = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
            if current_sales_person:
                filters["sales_person"] = current_sales_person
            else:
                # If no sales_person is provided and current user is not an employee, return empty list
                return []


        if from_date:
            from_date = getdate(from_date)
        if to_date:
            to_date = getdate(to_date)

        if from_date and to_date:
            filters["checkin_time"] = ["between", (from_date, to_date)] # Filter by checkin_time
        elif from_date:
            filters["checkin_time"] = [">=", from_date]
        elif to_date:
            filters["checkin_time"] = ["<=", to_date]

        if customer:
            filters["customer"] = customer

        frappe.log_error(f"get_sales_activity_monitoring_data: Querying Sales Activity Monitoring with filters: {filters}", "Sales Activity Monitoring Debug")
        raw_activities = frappe.db.get_list(
            "Sales Activity Monitoring", # Querying Sales Activity Monitoring DocType
            filters=filters,
            fields=[
                "name", # ID
                "employee_name", # Sales Name
                "customer", # Customer Name
                "plan_date_time", # Plan Date
                "checkin_time", # Visit Date (Checkin)
                "checkout_time", # Visit Date (Checkout)
                "duration", # Duration (already calculated in DocType)
                "image_link", # Photo
                "map_link", # Map
                "latitude", # For Map View
                "longitude", # For Map View
                "status", # Status
            ],
            order_by="checkin_time desc" # Order by checkin_time
        )

        activities = []
        for d in raw_activities:
            activity = dict(d)

            # Fetch customer address for hover
            customer_address = frappe.db.get_value("Customer", activity.get("customer"), "primary_address")
            if customer_address:
                activity["customer_address"] = customer_address.replace('<br>', ' ').replace('<br/>', ' ') # Clean up address
            else:
                activity["customer_address"] = ""

            activities.append(activity)

        return activities
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_sales_activity_monitoring_data")
        frappe.throw(f"Failed to fetch sales activity monitoring data: {e}")

@frappe.whitelist()
def create_sales_visit_plan(sales_visit_plan_data):
    try:
        # 1. Buat dokumen Sales Visit Plan baru
        doc = frappe.new_doc("Sales Visit Plan")

        # 2. Set bidang parent
        doc.sales_person = sales_visit_plan_data.get("sales_person")
        doc.planned_visit_date = sales_visit_plan_data.get("planned_visit_date")
        # Frappe akan menangani naming_series dan status default (Draft) secara otomatis

        # 3. Tambahkan entri child table
        for item_data in sales_visit_plan_data.get("visit_plan_details", []):
            child_doc = doc.append("visit_plan_details", {})
            child_doc.customer = item_data.get("customer")
            child_doc.address = item_data.get("address")
            child_doc.visit_time = item_data.get("visit_time")
            child_doc.notes = item_data.get("notes")
            # Status for child items is not explicitly passed from frontend as per new requirements,
            # but if it were, it would be set here. For now, it will default in Frappe.
            # child_doc.status = item_data.get("status")

        # 4. Sisipkan dokumen
        doc.insert()
        frappe.db.commit()

        return {"status": "success", "message": "Sales Visit Plan created successfully", "name": doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in create_sales_visit_plan")
        return {"status": "error", "message": str(e)}