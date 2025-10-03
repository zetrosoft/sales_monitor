import frappe
from frappe.auth import LoginManager
from frappe.utils import (
    add_days,
    get_datetime,
    get_first_day,
    get_first_day_of_week,
    get_last_day,
    get_last_day_of_week,
    getdate,
    now_datetime,
)


@frappe.whitelist(allow_guest=True)
def pwa_login(usr, pwd):
    try:
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
        employee_id = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not employee_id:
            frappe.throw("Employee ID not found for current user.")

        sales_person_id = frappe.db.get_value("Sales Person", {"employee": employee_id}, "name")
        if not sales_person_id:
            frappe.throw(f"Could not find linked Sales Person for Employee: {employee_id}")

        parent_plans = frappe.db.get_all(
            "Sales Visit Plan",
            filters=[["sales_person", "in", [sales_person_id, employee_id]]],
            fields=["name", "planned_visit_date", "docstatus"]
        )

        if not parent_plans:
            return []

        parent_plan_names = [p["name"] for p in parent_plans]
        plan_dates = {p["name"]: p["planned_visit_date"] for p in parent_plans}
        plan_statuses = {p["name"]: p["docstatus"] for p in parent_plans}

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
            fields=["sales_visit_plan_item", "checkin_time", "checkout_time", "duration", "map_link", "image_link", "latitude", "longitude"]
        )

        activity_details = {}
        for doc in activity_docs:
            activity_details[doc.sales_visit_plan_item] = {
                "checkin_time": doc.checkin_time,
                "checkout_time": doc.checkout_time,
                "duration": doc.duration,
                "map_link": doc.map_link,
                "image_link": doc.image_link,
                "latitude": doc.latitude,
                "longitude": doc.longitude
            }

        processed_items = []
        for item in visit_items:
            processed_item = dict(item)
            if not processed_item.get('status'):
                processed_item['status'] = 'Planned'

            parent_name = processed_item.get("parent")
            planned_date = plan_dates.get(parent_name)
            visit_time = processed_item.get('visit_time')

            processed_item['parent_docstatus'] = plan_statuses.get(parent_name, 0)

            if planned_date and visit_time:
                processed_item['planned_visit_time'] = f"{frappe.utils.format_date(planned_date, 'dd-MM-yyyy')} {frappe.utils.format_time(visit_time, 'HH:mm')}"
            elif planned_date:
                processed_item['planned_visit_time'] = frappe.utils.format_date(planned_date, 'dd-MM-yyyy')
            else:
                processed_item['planned_visit_time'] = visit_time or ''

            activities = activity_details.get(item.name, {})
            checkin_time = activities.get('checkin_time')
            checkout_time = activities.get('checkout_time')

            if checkin_time:
                dt_obj = frappe.utils.get_datetime(checkin_time)
                processed_item['checkin_time'] = dt_obj.strftime('%d-%m-%Y %H:%M:%S')
            if checkout_time:
                dt_obj = frappe.utils.get_datetime(checkout_time)
                processed_item['checkout_time'] = dt_obj.strftime('%d-%m-%Y %H:%M:%S')

            processed_item.update(activities)

            processed_item['sort_key_date'] = planned_date or frappe.utils.getdate('1900-01-01')
            processed_item['sort_key_time'] = visit_time or '00:00:00'

            processed_item.pop('visit_time', None)

            processed_items.append(processed_item)

        processed_items.sort(key=lambda x: (STATUS_ORDER.get(x.get('status', 'Draft'), 99), x['sort_key_date'], x['sort_key_time']))

        limit_start = int(limit_start)
        limit_page_length = int(limit_page_length)
        total_items = len(processed_items)
        paginated_items = processed_items[limit_start : limit_start + limit_page_length]

        for item in paginated_items:
            del item['sort_key_date']
            del item['sort_key_time']

        return {"data": paginated_items, "total": total_items}

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

from frappe.utils.file_manager import save_file


@frappe.whitelist()
def submit_visit_update(name, new_status, latitude=None, longitude=None, photo=None, checkout_time=None):
    try:
        doc = frappe.get_doc("Sales Visit Plan Item", name)
        parent_doc = frappe.get_doc("Sales Visit Plan", doc.parent)

        photo_url = None

        if photo:
            file_doc = save_file(photo.filename, photo.stream.read(), "Sales Activity Monitoring", name)
            photo_url = file_doc.file_url

        elif frappe.request.files:
            files = frappe.request.files.getlist("photo")
            if files:
                file_doc = save_file(files[0].filename, files[0].stream.read(), "Sales Activity Monitoring", name)
                photo_url = file_doc.file_url

        if new_status == "Checked In":
            doc.status = "Checked In"

            activity = frappe.new_doc("Sales Activity Monitoring")
            employee_id = parent_doc.sales_person
            activity.sales_person = employee_id
            employee_name = frappe.db.get_value("Employee", employee_id, "employee_name")
            activity.employee_name = employee_name
            activity.customer = doc.customer
            activity.sales_visit_plan_item = name
            activity.checkin_time = now_datetime()
            activity.status = "Checked In"
            activity.notes = doc.notes

            if parent_doc.planned_visit_date and doc.visit_time:
                activity.plan_date_time = f"{parent_doc.planned_visit_date} {doc.visit_time}"

            if latitude and longitude:
                activity.map_link = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=15/{latitude}/{longitude}"
                activity.latitude = latitude
                activity.longitude = longitude

            try:
                activity.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Kesalahan saat Insert Sales Activity")
                frappe.throw(f"Gagal menyimpan aktivitas : {e}")

        elif new_status == "Completed":
            doc.status = "Completed"

            activities = frappe.get_all(
                "Sales Activity Monitoring",
                filters={"sales_visit_plan_item": name, "status": "Checked In"},
                fields=["name"]
            )

            if activities:
                activity_name = activities[0].name
                activity = frappe.get_doc("Sales Activity Monitoring", activity_name)

                if checkout_time:
                    activity.checkout_time = frappe.utils.get_datetime(checkout_time)
                else:
                    activity.checkout_time = now_datetime()

                activity.status = "Completed"

                if photo_url:
                    activity.image_link = photo_url

                if latitude and longitude:
                    activity.map_link = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=15/{latitude}/{longitude}"
                    activity.latitude = latitude
                    activity.longitude = longitude

                if activity.checkin_time and activity.checkout_time:
                    duration_seconds = (activity.checkout_time - activity.checkin_time).total_seconds()
                    activity.duration = round(duration_seconds / 60)

                activity.save(ignore_permissions=True)
            else:
                frappe.log_error("Could not find a 'Checked In' Sales Activity Monitoring doc for checkout.", f"Sales Visit Plan Item: {name}")

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
            filters={"customer_name": store_name},
            fields=["name as order_id", "transaction_date as date", "grand_total as total"],
            order_by="transaction_date desc",
            limit=5
        )
        return [dict(d) for d in raw_orders]
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_order_history")
        frappe.throw(f"Failed to fetch order history: {e}")

@frappe.whitelist(allow_guest=True)
def get_employee_id(user_id):
    try:
        return frappe.db.get_value("Employee", {"user_id": user_id}, "name")
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
        employee_id = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not employee_id:
            frappe.throw("Employee ID not found for current user.")

        sales_person_id = frappe.db.get_value("Sales Person", {"employee": employee_id}, "name")
        if not sales_person_id:
            frappe.throw(f"Could not find linked Sales Person for Employee: {employee_id}")

        filters = [["sales_person", "in", [sales_person_id, employee_id]]]

        if from_date:
            from_date = getdate(from_date)
        if to_date:
            to_date = getdate(to_date)

        if from_date and to_date:
            filters.append(["checkin_time", "between", (from_date, to_date)])
        elif from_date:
            filters.append(["checkin_time", ">=", from_date])
        elif to_date:
            filters.append(["checkin_time", "<=", to_date])

        if customer:
            filters.append(["customer", "like", f"%{customer}%"])

        raw_activities = frappe.db.get_list(
            "Sales Activity Monitoring",
            filters=filters,
            fields=["checkin_time", "checkout_time", "customer", "duration", "status"],
            order_by="checkin_time desc"
        )

        activities = []
        for d in raw_activities:
            activity = dict(d)
            formatted_activity = {
                "Date": frappe.utils.format_date(activity.get("checkin_time")) if activity.get("checkin_time") else "",
                "Customer": activity.get("customer"),
                "Checkin": frappe.utils.format_time(activity.get("checkin_time")) if activity.get("checkin_time") else "",
                "Checkout": frappe.utils.format_time(activity.get("checkout_time")) if activity.get("checkout_time") else "",
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
        employee_id = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not employee_id:
            return {"status": "error", "message": "Employee not found for the current user."}

        sales_person = frappe.db.get_value("Sales Person", {"employee": employee_id}, "name")
        if not sales_person:
            return {"status": "error", "message": f"Akun Anda belum terhubung dengan profil Sales Person. Hubungi administrator untuk menautkan Employee ID: {employee_id}."}

        # Get all parent Sales Visit Plan names for today
        today_parent_plans = frappe.db.get_list(
            "Sales Visit Plan",
            filters=[
                ["sales_person", "in", [sales_person, employee_id]],
                ["planned_visit_date", "=", today_date]
            ],
            fields=["name"]
        )
        parent_plan_name_list = [p.name for p in today_parent_plans] if today_parent_plans else []

        total_visits_today = 0
        completed_visits_today = 0

        if parent_plan_name_list:
            total_visits_today = frappe.db.count(
                "Sales Visit Plan Item",
                filters=[["parent", "in", parent_plan_name_list]]
            )
            completed_visits_today = frappe.db.count(
                "Sales Visit Plan Item",
                filters=[
                    ["parent", "in", parent_plan_name_list],
                    ["status", "=", "Completed"]
                ]
            )

        # Get pending visits (Outstanding Visit) across all plans for the user
        all_parent_plans = frappe.db.get_all("Sales Visit Plan", filters={"sales_person": sales_person}, fields=["name"])
        all_parent_plan_names = [p.name for p in all_parent_plans]

        pending_visits = 0
        if all_parent_plan_names:
            pending_visits = frappe.db.count(
                "Sales Visit Plan Item",
                filters=[
                    ["parent", "in", all_parent_plan_names],
                    ["status", "in", ["", " ", "Draft", "Planned", "Checked In"]]
                ]
            )

        achievement_percentage = (completed_visits_today / total_visits_today) * 100 if total_visits_today > 0 else 0

        return {
            "status": "success",
            "total_visits_today": total_visits_today,
            "completed_visits_today": completed_visits_today,
            "pending_visits": pending_visits,
            "achievement_percentage": achievement_percentage,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error in get_dashboard_data for {sales_person} on {today_date}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_weekly_visit_sales_comparison_data():
    try:
        # Get the Employee ID for the current logged-in user.
        employee_id = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not employee_id:
            return {"status": "error", "message": "Employee not found for the current user."}

        # Log the found Employee ID for debugging purposes
        frappe.log(f"Debug: Found Employee ID: {employee_id}")

        today = get_datetime(frappe.utils.today())
        weekly_data = {}

        for i in range(8): # Last 8 weeks
            week_start = get_first_day_of_week(add_days(today, -7 * i))

            week_number = week_start.isocalendar()[1]
            week_label = f"Minggu ke-{week_number}"

            # Filter now uses the 'employee' field directly, as per the correct doctype setup.
            parent_plans_in_week = frappe.db.get_list(
                "Sales Visit Plan",
                filters={
                    "sales_person": employee_id,  # CORRECTED FILTER
                    "planned_visit_date": ["between", [week_start, add_days(week_start, 6)]]
                },
                fields=["name"]
            )
            frappe.log(f"Debug: Week {week_start}, Plans: {parent_plans_in_week}")
            plan_names_in_week = [p.name for p in parent_plans_in_week]

            planned_in_week = 0
            completed_in_week = 0

            if plan_names_in_week:
                planned_in_week = frappe.db.count(
                    "Sales Visit Plan Item",
                    filters={"parent": ["in", plan_names_in_week]}
                )
                completed_in_week = frappe.db.count(
                    "Sales Visit Plan Item",
                    filters={
                        "parent": ["in", plan_names_in_week],
                        "status": "Completed"
                    }
                )

            weekly_data[week_label] = {
                "planned": planned_in_week,
                "completed": completed_in_week
            }

        labels = list(weekly_data.keys())
        planned_data = [weekly_data[label]["planned"] for label in labels]
        completed_data = [weekly_data[label]["completed"] for label in labels]

        return {
            "status": "success",
            "labels": labels,
            "datasets": [
                {"label": "Planned", "data": planned_data},
                {"label": "Completed", "data": completed_data},
            ]
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_weekly_visit_sales_comparison_data")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_weekly_customer_order_data():
    try:
        employee_id = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not employee_id:
            return {"status": "error", "message": "Employee not found for the current user."}

        sales_person = frappe.db.get_value("Sales Person", {"employee": employee_id}, "name")
        if not sales_person:
            return {"status": "error", "message": f"Akun Anda belum terhubung dengan profil Sales Person. Hubungi administrator untuk menautkan Employee ID: {employee_id}."}

        today = get_datetime(frappe.utils.today())

        customer_weekly_orders = {}

        for i in range(8): # Last 8 weeks
            week_start = get_first_day_of_week(add_days(today, -7 * i))
            week_end = get_last_day_of_week(add_days(today, -7 * i))
            week_label = f"Minggu ke-{week_start.isocalendar()[1]}"

            orders_in_week = frappe.db.get_list(
                "Sales Order",
                filters={
                    "sales_person": sales_person,
                    "transaction_date": ["between", [week_start, week_end]],
                    "docstatus": 1
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

        formatted_data = []
        all_customers = set()
        for week_data in customer_weekly_orders.values():
            for customer in week_data.keys():
                all_customers.add(customer)

        sorted_customers = sorted(list(all_customers))

        for week_label, customers_data in customer_weekly_orders.items():
            row = {"week": week_label}
            for customer in sorted_customers:
                row[customer] = customers_data.get(customer, 0)
            formatted_data.append(row)

        return {"status": "success", "data": formatted_data, "customers": sorted_customers}

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
            employee_id = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
            if employee_id:
                sales_person_id = frappe.db.get_value("Sales Person", {"employee": employee_id}, "name")
                possible_ids = [employee_id]
                if sales_person_id and sales_person_id not in possible_ids:
                    possible_ids.append(sales_person_id)
                filters["sales_person"] = ["in", possible_ids]
            else:
                return []

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
            filters["customer"] = customer

        raw_activities = frappe.db.get_list(
            "Sales Activity Monitoring",
            filters=filters,
            fields=[
                "name", "employee_name", "customer", "plan_date_time", "checkin_time",
                "checkout_time", "duration", "image_link", "map_link", "latitude",
                "longitude", "status"
            ],
            order_by="checkin_time desc"
        )

        activities = []
        for d in raw_activities:
            activity = dict(d)
            customer_address = frappe.db.get_value("Customer", activity.get("customer"), "primary_address")
            activity["customer_address"] = customer_address.replace('<br>', ' ').replace('<br/>', ' ') if customer_address else ""
            activities.append(activity)

        return activities
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_sales_activity_monitoring_data")
        frappe.throw(f"Failed to fetch sales activity monitoring data: {e}")

@frappe.whitelist()
def create_sales_visit_plan(sales_visit_plan_data):
    try:
        doc = frappe.new_doc("Sales Visit Plan")
        doc.sales_person = sales_visit_plan_data.get("sales_person")
        doc.planned_visit_date = sales_visit_plan_data.get("planned_visit_date")

        for item_data in sales_visit_plan_data.get("visit_plan_details", []):
            doc.append("visit_plan_details", {
                "customer": item_data.get("customer"),
                "address": item_data.get("address"),
                "visit_time": item_data.get("visit_time"),
                "notes": item_data.get("notes"),
            })

        doc.insert()
        frappe.db.commit()

        return {"status": "success", "message": "Sales Visit Plan created successfully", "name": doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in create_sales_visit_plan")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_customer_master_location(customer):
    """
    Fetches the latitude and longitude from the very first recorded visit
    for a given customer to be used as the 'master' location.
    """
    if not customer:
        return None

    first_visit = frappe.db.get_list(
        "Sales Activity Monitoring",
        filters={
            "customer": customer,
            "latitude": ["!=", 0],
            "longitude": ["!=", 0],
        },
        fields=["latitude", "longitude"],
        order_by="creation asc",
        limit=1,
    )

    if first_visit:
        return {
            "latitude": first_visit[0].get("latitude"),
            "longitude": first_visit[0].get("longitude"),
        }
    return None
