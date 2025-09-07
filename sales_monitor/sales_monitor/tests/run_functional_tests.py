import frappe
from frappe.utils import getdate, now_datetime

def run_functional_tests():
    print("\n--- Starting Automated Functional Tests ---")

    # --- Setup: Create Dummy Data ---
    print("Creating dummy data...")
    try:
        # Clean up any existing test data
        frappe.db.sql("DELETE FROM `tabSales Activity Log`")
        frappe.db.sql("DELETE FROM `tabSales Visit Plan Item`")
        frappe.db.sql("DELETE FROM `tabSales Visit Plan`")
        frappe.db.sql("DELETE FROM `tabEmployee` WHERE name = 'Test Sales Person'")
        frappe.db.sql("DELETE FROM `tabCustomer` WHERE name = 'Test Customer'")
        frappe.db.sql("DELETE FROM `tabUser` WHERE email = 'test_sales@example.com'")
        frappe.db.commit()

        # Create a dummy User
        if not frappe.db.exists("User", "test_sales@example.com"):
            test_user = frappe.get_doc({
                "doctype": "User",
                "email": "test_sales@example.com",
                "first_name": "Test",
                "last_name": "Sales",
                "enabled": 1,
                "new_password": "password",
                "roles": [{"role": "Sales User"}]
            }).insert(ignore_permissions=True)
        else:
            test_user = frappe.get_doc("User", "test_sales@example.com")

        # Create a dummy Sales Person (Employee)
        if not frappe.db.exists("Employee", "Test Sales Person"):
            sales_person = frappe.get_doc({
                "doctype": "Employee",
                "employee_name": "Test Sales Person",
                "user_id": test_user.name
            }).insert(ignore_permissions=True)
        else:
            sales_person = frappe.get_doc("Employee", "Test Sales Person")

        # Create a dummy Customer
        if not frappe.db.exists("Customer", "Test Customer"):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "Test Customer"
            }).insert(ignore_permissions=True)
        else:
            customer = frappe.get_doc("Customer", "Test Customer")

        # Create a dummy Sales Visit Plan
        sales_visit_plan = frappe.get_doc({
            "doctype": "Sales Visit Plan",
            "sales_person": sales_person.name,
            "planned_visit_date": getdate(),
            "status": "Planned",
            "visit_plan_details": []
        }).insert(ignore_permissions=True)

        # Create a dummy Sales Visit Plan Item
        sales_visit_plan_item = frappe.get_doc({
            "doctype": "Sales Visit Plan Item",
            "parent": sales_visit_plan.name,
            "parenttype": "Sales Visit Plan",
            "parentfield": "visit_plan_details",
            "customer": customer.name,
            "address": "Test Address",
            "visit_time": "10:00:00",
            "notes": "Initial notes",
            "status": "Planned"
        }).insert(ignore_permissions=True)

        # Link the item to the parent plan
        sales_visit_plan.append("visit_plan_details", {
            "customer": customer.name,
            "address": "Test Address",
            "visit_time": "10:00:00",
            "notes": "Initial notes",
            "status": "Planned"
        })
        sales_visit_plan.save(ignore_permissions=True)
        frappe.db.commit()
        print("Dummy data created successfully.")

    except Exception as e:
        print(f"Error during dummy data setup: {e}")
        frappe.log_error(frappe.get_traceback(), "Automated Functional Test Setup Error")
        return # Exit if setup fails

    # --- Test update_sales_visit_plan_status (Check-in) ---
    print("\nTesting Check-in API...")
    try:
        from sales_monitor.api import update_sales_visit_plan_status
        
        latitude_in = "1.2345"
        longitude_in = "6.7890"
        photo_url_in = "/files/test_checkin.jpg"
        
        response_in = update_sales_visit_plan_status(
            name=sales_visit_plan_item.name,
            new_status="Checked In",
            latitude=latitude_in,
            longitude=longitude_in,
            photo_url=photo_url_in
        )
        frappe.db.commit()
        print(f"Check-in API Response: {response_in}")

        # Verify Sales Activity Log created
        activity_log_in = frappe.get_list(
            "Sales Activity Log",
            filters={
                "sales_visit_plan_item": sales_visit_plan_item.name,
                "activity_type": "Check-in"
            },
            fields=["actual_location_latitude", "actual_location_longitude", "check_in_photo"]
        )
        assert len(activity_log_in) == 1, "Check-in Sales Activity Log not created."
        assert activity_log_in[0].actual_location_latitude == latitude_in, "Check-in latitude mismatch."
        assert activity_log_in[0].actual_location_longitude == longitude_in, "Check-in longitude mismatch."
        assert activity_log_in[0].check_in_photo == photo_url_in, "Check-in photo mismatch."

        # Verify Sales Visit Plan Item status updated
        updated_item_in = frappe.get_doc("Sales Visit Plan Item", sales_visit_plan_item.name)
        assert updated_item_in.status == "Checked In", "Sales Visit Plan Item status not updated to Checked In."
        print("Check-in API test successful.")

    except Exception as e:
        print(f"Error during Check-in API test: {e}")
        frappe.log_error(frappe.get_traceback(), "Automated Functional Test Check-in Error")

    # --- Test update_sales_visit_plan_status (Check-out) ---
    print("\nTesting Check-out API...")
    try:
        latitude_out = "9.8765"
        longitude_out = "4.3210"
        photo_url_out = "/files/test_checkout.jpg"

        response_out = update_sales_visit_plan_status(
            name=sales_visit_plan_item.name,
            new_status="Completed",
            latitude=latitude_out,
            longitude=longitude_out,
            photo_url=photo_url_out
        )
        frappe.db.commit()
        print(f"Check-out API Response: {response_out}")

        # Verify Sales Activity Log created for checkout
        activity_log_out = frappe.get_list(
            "Sales Activity Log",
            filters={
                "sales_visit_plan_item": sales_visit_plan_item.name,
                "activity_type": "Checkout"
            },
            fields=["actual_location_latitude", "actual_location_longitude", "check_out_photo"]
        )
        assert len(activity_log_out) == 1, "Check-out Sales Activity Log not created."
        assert activity_log_out[0].actual_location_latitude == latitude_out, "Check-out latitude mismatch."
        assert activity_log_out[0].actual_location_longitude == longitude_out, "Check-out longitude mismatch."
        assert activity_log_out[0].check_out_photo == photo_url_out, "Check-out photo mismatch."

        # Verify Sales Visit Plan Item status updated
        updated_item_out = frappe.get_doc("Sales Visit Plan Item", sales_visit_plan_item.name)
        assert updated_item_out.status == "Completed", "Sales Visit Plan Item status not updated to Completed."
        print("Check-out API test successful.")

    except Exception as e:
        print(f"Error during Check-out API test: {e}")
        frappe.log_error(frappe.get_traceback(), "Automated Functional Test Check-out Error")

    # --- Test get_sales_activity_monitoring_data ---
    print("\nTesting get_sales_activity_monitoring_data...")
    try:
        from sales_monitor.api import get_sales_activity_monitoring_data

        # Test with no filters
        data_no_filter = get_sales_activity_monitoring_data()
        assert len(data_no_filter) > 0, "No data returned for get_sales_activity_monitoring_data with no filters."
        assert data_no_filter[0]["sales_person"] == sales_person.name, "Sales Person mismatch."
        assert data_no_filter[0]["customer"] == customer.name, "Customer mismatch."
        assert data_no_filter[0]["status"] == "Completed", "Status mismatch."
        assert data_no_filter[0]["checkin_time"] is not None, "Checkin time is None."
        assert data_no_filter[0]["checkout_time"] is not None, "Checkout time is None."
        assert data_no_filter[0]["duration"] > 0, "Duration is not greater than 0."
        assert data_no_filter[0]["map_link"] is not None, "Map link is None."
        assert data_no_filter[0]["image_link"] is not None, "Image link is None."
        print("get_sales_activity_monitoring_data (no filter) test successful.")

        # Test with sales_person filter
        data_filtered_sp = get_sales_activity_monitoring_data(sales_person=sales_person.name)
        assert len(data_filtered_sp) > 0, "No data returned for sales_person filter."
        assert data_filtered_sp[0]["sales_person"] == sales_person.name, "Sales Person filter mismatch."
        print("get_sales_activity_monitoring_data (sales_person filter) test successful.")

        # Test with customer filter
        data_filtered_cust = get_sales_activity_monitoring_data(customer=customer.name)
        assert len(data_filtered_cust) > 0, "No data returned for customer filter."
        assert data_filtered_cust[0]["customer"] == customer.name, "Customer filter mismatch."
        print("get_sales_activity_monitoring_data (customer filter) test successful.")

        # Test with date filter (today)
        data_filtered_date = get_sales_activity_monitoring_data(from_date=getdate(), to_date=getdate())
        assert len(data_filtered_date) > 0, "No data returned for date filter."
        assert frappe.utils.getdate(data_filtered_date[0]["plan_date_time"]) == getdate(), "Date filter mismatch."
        print("get_sales_activity_monitoring_data (date filter) test successful.")

        # Test with non-matching filter
        data_filtered_nomatch = get_sales_activity_monitoring_data(sales_person="NonExistent Sales Person")
        assert len(data_filtered_nomatch) == 0, "Data returned for non-matching filter."
        print("get_sales_activity_monitoring_data (non-matching filter) test successful.")

    except Exception as e:
        print(f"Error during get_sales_activity_monitoring_data test: {e}")
        frappe.log_error(frappe.get_traceback(), "Automated Functional Test Get Data Error")

    finally:
        # --- Cleanup: Delete Dummy Data ---
        print("\nCleaning up dummy data...")
        try:
            frappe.db.sql("DELETE FROM `tabSales Activity Log`")
            frappe.db.sql("DELETE FROM `tabSales Visit Plan Item`")
            frappe.db.sql("DELETE FROM `tabSales Visit Plan`")
            frappe.db.sql("DELETE FROM `tabEmployee` WHERE name = 'Test Sales Person'")
            frappe.db.sql("DELETE FROM `tabCustomer` WHERE name = 'Test Customer'")
            frappe.db.sql("DELETE FROM `tabUser` WHERE email = 'test_sales@example.com'")
            frappe.db.commit()
            print("Dummy data cleaned up successfully.")
        except Exception as e:
            print(f"Error during dummy data cleanup: {e}")
            frappe.log_error(frappe.get_traceback(), "Automated Functional Test Cleanup Error")

    print("\n--- Automated Functional Tests Completed ---")

# To run this script, use: bench --site your_site_name execute sales_monitor.tests.run_functional_tests.run_functional_tests
