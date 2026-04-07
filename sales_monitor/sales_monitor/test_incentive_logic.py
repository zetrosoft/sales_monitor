import frappe
from frappe.utils import getdate, get_first_day, get_last_day
from sales_monitor.api import get_net_turnover, get_join_new_bonus, get_incentive_tier
from frappe.exceptions import ValidationError

def setup_dummy_data():
    """Clears existing dummy data and sets up new data for testing."""
    print("Setting up dummy data...")

    # Clear existing dummy data (careful in production!)
    cleanup_dummy_data()

    # Ensure _Test Company exists
    create_if_not_exists("Company", {"company_name": "_Test Company"}, {"doctype": "Company", "company_name": "_Test Company"})
    # Ensure All Item Groups exists
    create_if_not_exists("Item Group", {"item_group_name": "All Item Groups"}, {"doctype": "Item Group", "item_group_name": "All Item Groups"})


    # 1. Create Roles
    create_if_not_exists("Role", {"name": "Sales User"}, {"doctype": "Role", "role_name": "Sales User"})
    create_if_not_exists("Role", {"name": "Sales Manager"}, {"doctype": "Role", "role_name": "Sales Manager"})
    create_if_not_exists("Role", {"name": "System Manager"}, {"doctype": "Role", "role_name": "System Manager"})


    # 2. Create Employees, Sales Persons, Users, and assign roles
    # Budi (Salesman)
    budi_user = create_user_employee_salesperson("budi_salesman@example.com", "Budi Salesman", "Sales User")
    # Siti (Admin Sales)
    siti_user = create_user_employee_salesperson("siti_adminsales@example.com", "Siti Admin Sales", "Sales User")
    # Andi (SPV Sales)
    andi_user = create_user_employee_salesperson("andi_spvsales@example.com", "Andi SPV Sales", "Sales Manager")

    # 3. Create Customer Groups
    create_if_not_exists("Customer Group", {"customer_group_name": "Distributor"}, {"doctype": "Customer Group", "customer_group_name": "Distributor"})
    create_if_not_exists("Customer Group", {"customer_group_name": "Retail"}, {"doctype": "Customer Group", "customer_group_name": "Retail"})
    create_if_not_exists("Customer Group", {"customer_group_name": "Reseller"}, {"doctype": "Customer Group", "customer_group_name": "Reseller"})
    
    create_item("Item 1") # Ensure Item 1 exists for Sales Invoice

    # 4. Create Customers and link to Sales Persons
    # Budi's customers
    budi_cust1 = create_customer("Budi_Cust_A", budi_user["sales_person"], "Retail")
    budi_cust2 = create_customer("Budi_Cust_B", budi_user["sales_person"], "Retail")
    budi_cust3 = create_customer("Budi_Cust_C_New", budi_user["sales_person"], "Reseller") # New customer for Join New bonus

    # Siti's customers
    siti_cust1 = create_customer("Siti_Cust_X", siti_user["sales_person"], "Retail")
    siti_cust2 = create_customer("Siti_Cust_Y", siti_user["sales_person"], "Reseller")

    # Andi's customers (Distributors)
    andi_cust1 = create_customer("Andi_Dist_1", andi_user["sales_person"], "Distributor")
    andi_cust2 = create_customer("Andi_Dist_2", andi_user["sales_person"], "Distributor")
    andi_cust3 = create_customer("Andi_Dist_3_New", andi_user["sales_person"], "Distributor") # New customer for Join New bonus

    # 5. Create Sales Incentive Settings (using create_incentive_data.py)
    # Ensure this script creates the Admin Sales and SPV Sales settings correctly.
    # It will automatically delete and recreate, so no need to filter existing
    from sales_monitor import create_incentive_data
    create_incentive_data.create_sales_incentive_data()
    print("Sales Incentive Settings created/updated.")

    # 6. Create Sales Invoices for January 2026
    jan_2026_start = get_first_day("2026-01-01")
    jan_2026_end = get_last_day("2026-01-01")

    # Budi's invoices (1.5M total)
    create_sales_invoice(budi_cust1, budi_user["sales_person"], 700000000, "2026-01-10")
    create_sales_invoice(budi_cust2, budi_user["sales_person"], 800000000, "2026-01-15")
    # One return for Budi to test net turnover
    create_sales_invoice(budi_cust1, budi_user["sales_person"], 100000000, "2026-01-20", is_return=1) # Net = 1.4M

    # Siti's invoices (2.5M total)
    create_sales_invoice(siti_cust1, siti_user["sales_person"], 1200000000, "2026-01-05")
    create_sales_invoice(siti_cust2, siti_user["sales_person"], 1300000000, "2026-01-25")

    # Andi's invoices (2.0M total from Distributors)
    create_sales_invoice(andi_cust1, andi_user["sales_person"], 900000000, "2026-01-08")
    create_sales_invoice(andi_cust2, andi_user["sales_person"], 1100000000, "2026-01-18")

    # Join New Invoices (first invoices in period for new customers)
    # Budi: Reseller (Order Awal >= 500k)
    create_sales_invoice(budi_cust3, budi_user["sales_person"], 1000000, "2026-01-03", is_new_customer=True) # Matches 500k tier for Reseller
    # Create 9 more dummy new customers for Budi to meet 10 resellers
    for i in range(1,10):
        new_cust = create_customer(f"Budi_Cust_New_{i}", budi_user["sales_person"], "Reseller")
        create_sales_invoice(new_cust, budi_user["sales_person"], 600000, "2026-01-05", is_new_customer=True)

    # Andi: Distributor (Order Awal >= 100M)
    create_sales_invoice(andi_cust3, andi_user["sales_person"], 150000000, "2026-01-02", is_new_customer=True) # Matches 100M tier for Distributor

    print("Dummy data setup complete.")

def cleanup_dummy_data():
    """Deletes dummy data created by setup_dummy_data."""
    print("Cleaning up dummy data...")
    # Order of deletion is important due to dependencies
    frappe.db.sql("DELETE FROM `tabSales Incentive Payment Item`")
    frappe.db.sql("DELETE FROM `tabSales Incentive Payment`")
    frappe.db.sql("DELETE FROM `tabSales Invoice` WHERE customer LIKE 'Budi_Cust_%' OR customer LIKE 'Siti_Cust_%' OR customer LIKE 'Andi_Dist_%'")
    frappe.db.sql("DELETE FROM `tabCustomer` WHERE name LIKE 'Budi_Cust_%' OR name LIKE 'Siti_Cust_%' OR name LIKE 'Andi_Dist_%'")
    frappe.db.sql("DELETE FROM `tabSales Person` WHERE employee LIKE 'EMP-Budi%' OR employee LIKE 'EMP-Siti%' OR employee LIKE 'EMP-Andi%'")
    frappe.db.sql("DELETE FROM `tabEmployee` WHERE name LIKE 'EMP-Budi%' OR name LIKE 'EMP-Siti%' OR employee LIKE 'EMP-Andi%'")
    frappe.db.sql("DELETE FROM `tabUser` WHERE email IN ('budi_salesman@example.com', 'siti_adminsales@example.com', 'andi_spvsales@example.com')")
    frappe.db.sql("DELETE FROM `tabSales Incentive Setting` WHERE name IN ('Bonus Admin Sales 2026', 'Bonus SPV Sales 2026')")
    frappe.db.sql("DELETE FROM `tabCompany` WHERE name = '_Test Company'") # Clean up test company
    frappe.db.sql("DELETE FROM `tabItem` WHERE name = 'Item 1'") # Clean up test item
    frappe.db.sql("DELETE FROM `tabItem Group` WHERE name = 'All Item Groups'")
    print("Dummy data cleanup complete.")


def create_if_not_exists(doctype, filters, data=None):
    if not frappe.db.exists(doctype, filters):
        print(f"DEBUG: Creating {doctype}: {filters.get('name') or filters.get(list(filters.keys())[0])}")
        try:
            doc = frappe.get_doc(data or filters)
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"DEBUG: Successfully created {doctype}: {doc.name}")
            return doc
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Error creating {doctype} {filters}: {e}")
            raise ValidationError(f"Error creating {doctype} {filters}: {e}")
    else:
        print(f"DEBUG: {doctype} already exists: {filters.get('name') or filters.get(list(filters.keys())[0])}")
    return frappe.get_doc(doctype, filters)

def create_user_employee_salesperson(email, full_name, role_name):
    print(f"DEBUG: Starting creation for {full_name}...")
    # User
    user_doc = create_if_not_exists("User", {"email": email}, {
        "doctype": "User", "email": email, "first_name": full_name.split()[0], "last_name": full_name.split()[-1],
        "send_welcome_email": 0, "enabled": 1, "new_password": "password", "enabled": 1 # Add password and enabled for full creation
    })
    if role_name not in frappe.get_roles(user_doc.name):
        user_doc.add_roles(role_name)
    #frappe.db.set_value("User", user_doc.name, "enabled", 1) # Ensure user is enabled
    user_doc.save(ignore_permissions=True)
    print(f"DEBUG: User {user_doc.name} created/updated with role {role_name}.")

    # Employee
    employee_id = f"EMP-{full_name.replace(' ', '')}"
    employee_doc = create_if_not_exists("Employee", {"employee_name": full_name}, {
        "doctype": "Employee", "employee_name": full_name, "company": "_Test Company", "user_id": user_doc.name,
        "first_name": full_name.split()[0], "last_name": full_name.split()[-1], "employee_number": employee_id,
        "designation": "Sales" # Add designation to prevent validation errors
    })
    print(f"DEBUG: Employee {employee_doc.name} created/updated.")
    
    # Sales Person
    sales_person_doc = create_if_not_exists("Sales Person", {"employee": employee_doc.name}, {
        "doctype": "Sales Person", "sales_person_name": full_name, "employee": employee_doc.name
    })

    print(f"DEBUG: Created/Retrieved Sales Person: {sales_person_doc.name} for {full_name}")
    return {"user": user_doc.name, "employee": employee_doc.name, "sales_person": sales_person_doc.name}

def create_customer(name, sales_person, customer_group):
    customer_doc = create_if_not_exists("Customer", {"customer_name": name}, {
        "doctype": "Customer", "customer_name": name, "customer_group": customer_group,
        "territory": "All Territories", "sales_person": sales_person, "customer_type": "Individual"
    })
    print(f"DEBUG: Created/Retrieved Customer: {customer_doc.name}")
    return customer_doc.name

def create_sales_invoice(customer, sales_person, grand_total, posting_date, is_return=0, is_new_customer=False):
    si_doc = frappe.new_doc("Sales Invoice")
    si_doc.customer = customer
    si_doc.posting_date = posting_date
    si_doc.due_date = posting_date # For simplicity
    si_doc.currency = "IDR"
    si_doc.company = "_Test Company"
    si_doc.sales_person = sales_person
    si_doc.grand_total = grand_total
    si_doc.set_total = grand_total
    si_doc.net_total = grand_total # For simplicity, ignore tax
    si_doc.is_return = is_return

    # Add a dummy item
    si_doc.append("items", {
        "item_code": "Item 1",
        "qty": 1,
        "rate": grand_total,
        "amount": grand_total
    })
    
    # Submit the invoice
    try:
        si_doc.insert(ignore_permissions=True)
        si_doc.submit()
        frappe.db.commit() # Commit after each invoice submission
        print(f"DEBUG: Created Sales Invoice: {si_doc.name} for {customer}, Total: {grand_total}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error creating Sales Invoice for {customer}: {e}")
        frappe.db.rollback() # Rollback on error
        raise
    return si_doc.name

def run_tests():
    print("\nRunning incentive logic tests...")
    jan_2026_start = get_first_day("2026-01-01")
    jan_2026_end = get_last_day("2026-01-01")

    # Get Sales Persons for testing
    print("DEBUG: Retrieving Sales Persons for testing...")
    budi_sp = frappe.db.get_value("Sales Person", {"sales_person_name": "Budi Salesman"})
    siti_sp = frappe.db.get_value("Sales Person", {"sales_person_name": "Siti Admin Sales"})
    andi_sp = frappe.db.get_value("Sales Person", {"sales_person_name": "Andi SPV Sales"})
    print(f"DEBUG: Budi SP: {budi_sp}, Siti SP: {siti_sp}, Andi SP: {andi_sp}")


    if not all([budi_sp, siti_sp, andi_sp]):
        frappe.log_error("Failed to retrieve all dummy sales persons. Setup might have failed. Check logs for creation errors.")
        raise ValidationError("Failed to retrieve all dummy sales persons. Setup might have failed. One or more SP are None.")

    # --- Test Budi (Sales User - Admin Sales Scheme) ---
    print("\n--- Testing Budi (Sales User - Admin Sales Scheme) ---")
    
    # Get Budi's incentive setting
    budi_setting_doc = frappe.get_doc("Sales Incentive Setting", "Bonus Admin Sales 2026")
    budi_customer_groups_filters = [g.customer_group for g in budi_setting_doc.customer_group_filter] if budi_setting_doc.customer_group_filter else []

    net_turnover_budi = get_net_turnover(budi_sp, jan_2026_start, jan_2026_end, budi_setting_doc.incentive_category, frappe.json.dumps(budi_customer_groups_filters))
    print(f"Budi Net Turnover: {net_turnover_budi}")
    # Expected: 1.5B (total sales) - 100M (return) = 1.4B
    assert abs(net_turnover_budi - 1400000000.0) < 0.01, f"Budi Net Turnover mismatch. Expected 1.4B, Got {net_turnover_budi}"

    join_new_budi = get_join_new_bonus(budi_sp, jan_2026_start, jan_2026_end)
    print(f"Budi Join New Bonus: {join_new_budi['total_bonus']}")
    # Expected: 10 Reseller * 5,000 = 50,000
    assert abs(join_new_budi["total_bonus"] - 50000.0) < 0.01, f"Budi Join New Bonus mismatch. Expected 50,000, Got {join_new_budi['total_bonus']}"

    tier_budi = get_incentive_tier(net_turnover_budi, budi_sp, jan_2026_start)
    print(f"Budi Tier Info: {tier_budi}")
    # Expected: 1.4B < 1.8B (min tier), so tier should be None or yield 0 bonus
    bonus_omset_budi = (net_turnover_budi * tier_budi["persentase"]) + tier_budi["bonus_admin"] if tier_budi else 0.0
    assert abs(bonus_omset_budi - 0.0) < 0.01, f"Budi Omset Bonus mismatch. Expected 0, Got {bonus_omset_budi}"
    #assert tier_budi is None or tier_budi.get("min_omset", 0) > net_turnover_budi, "Budi should not hit a tier."
    # If tier_budi is None, the assert above would fail.
    # The condition should be: if tier_budi is None, or if tier_budi exists but the amount is too low.
    if tier_budi:
        assert net_turnover_budi < tier_budi.get("min_omset", 0), "Budi should not hit a tier that gives bonus."


    total_budi = join_new_budi["total_bonus"] + bonus_omset_budi
    print(f"Budi Total Incentive: {total_budi}")
    assert abs(total_budi - 50000.0) < 0.01, f"Budi Total Incentive mismatch. Expected 50,000, Got {total_budi}"
    print("Budi tests passed.")

    # --- Test Siti (Sales User - Admin Sales Scheme) ---
    print("\n--- Testing Siti (Sales User - Admin Sales Scheme) ---")
    siti_setting_doc = frappe.get_doc("Sales Incentive Setting", "Bonus Admin Sales 2026")
    siti_customer_groups_filters = [g.customer_group for g in siti_setting_doc.customer_group_filter] if siti_setting_doc.customer_group_filter else []

    net_turnover_siti = get_net_turnover(siti_sp, jan_2026_start, jan_2026_end, siti_setting_doc.incentive_category, frappe.json.dumps(siti_customer_groups_filters))
    print(f"Siti Net Turnover: {net_turnover_siti}")
    # Expected: 2.5B
    assert abs(net_turnover_siti - 2500000000.0) < 0.01, f"Siti Net Turnover mismatch. Expected 2.5B, Got {net_turnover_siti}"

    join_new_siti = get_join_new_bonus(siti_sp, jan_2026_start, jan_2026_end)
    print(f"Siti Join New Bonus: {join_new_siti['total_bonus']}")
    # Expected: 0
    assert abs(join_new_siti["total_bonus"] - 0.0) < 0.01, f"Siti Join New Bonus mismatch. Expected 0, Got {join_new_siti['total_bonus']}"

    tier_siti = get_incentive_tier(net_turnover_siti, siti_sp, jan_2026_start)
    print(f"Siti Tier Info: {tier_siti}")
    # Expected: 2.5B falls into 2.5B tier (0.006% + 150k)
    assert tier_siti["min_omset"] == 2500000000.0, "Siti Tier min_omset mismatch"
    assert abs(tier_siti["persentase"] - 0.006) < 0.0001, "Siti Tier persentase mismatch"
    assert abs(tier_siti["bonus_admin"] - 150000.0) < 0.01, "Siti Tier bonus_admin mismatch"
    
    bonus_omset_siti = (net_turnover_siti * tier_siti["persentase"]) + tier_siti["bonus_admin"]
    print(f"Siti Omset Bonus: {bonus_omset_siti}")
    # Expected: (2.5B * 0.006%) + 150k = 150k + 150k = 300k
    assert abs(bonus_omset_siti - 300000.0) < 0.01, f"Siti Omset Bonus mismatch. Expected 300k, Got {bonus_omset_siti}"

    total_siti = join_new_siti["total_bonus"] + bonus_omset_siti
    print(f"Siti Total Incentive: {total_siti}")
    assert abs(total_siti - 300000.0) < 0.01, f"Siti Total Incentive mismatch. Expected 300k, Got {total_siti}"
    print("Siti tests passed.")

    # --- Test Andi (Sales Manager - SPV Sales Scheme) ---
    print("\n--- Testing Andi (Sales Manager - SPV Sales Scheme) ---")
    andi_setting_doc = frappe.get_doc("Sales Incentive Setting", "Bonus SPV Sales 2026")
    andi_customer_groups_filters = [g.customer_group for g in andi_setting_doc.customer_group_filter] if andi_setting_doc.customer_group_filter else []
    
    net_turnover_andi = get_net_turnover(andi_sp, jan_2026_start, jan_2026_end, andi_setting_doc.incentive_category, frappe.json.dumps(andi_customer_groups_filters))
    print(f"Andi Net Turnover: {net_turnover_andi}")
    # Expected: 2.0B (only Distributor)
    assert abs(net_turnover_andi - 2000000000.0) < 0.01, f"Andi Net Turnover mismatch. Expected 2.0B, Got {net_turnover_andi}"

    join_new_andi = get_join_new_bonus(andi_sp, jan_2026_start, jan_2026_end)
    print(f"Andi Join New Bonus: {join_new_andi['total_bonus']}")
    # Expected: 1 Distributor * 500,000 = 500,000
    assert abs(join_new_andi["total_bonus"] - 500000.0) < 0.01, f"Andi Join New Bonus mismatch. Expected 500,000, Got {join_new_andi['total_bonus']}"

    tier_andi = get_incentive_tier(net_turnover_andi, andi_sp, jan_2026_start)
    print(f"Andi Tier Info: {tier_andi}")
    # Expected: 2.0B falls into 2.0B tier (0.03% + 500k)
    assert tier_andi["min_omset"] == 2000000000.0, "Andi Tier min_omset mismatch"
    assert abs(tier_andi["persentase"] - 0.03) < 0.0001, "Andi Tier persentase mismatch"
    assert abs(tier_andi["bonus_admin"] - 500000.0) < 0.01, "Andi Tier bonus_admin mismatch"

    bonus_omset_andi = (net_turnover_andi * tier_andi["persentase"]) + tier_andi["bonus_admin"]
    print(f"Andi Omset Bonus: {bonus_omset_andi}")
    # Expected: (2.0B * 0.03%) + 500k = 600k + 500k = 1.1M
    assert abs(bonus_omset_andi - 1100000.0) < 0.01, f"Andi Omset Bonus mismatch. Expected 1.1M, Got {bonus_omset_andi}"

    total_andi = join_new_andi["total_bonus"] + bonus_omset_andi
    print(f"Andi Total Incentive: {total_andi}")
    assert abs(total_andi - 1600000.0) < 0.01, f"Andi Total Incentive mismatch. Expected 1.6M, Got {total_andi}"
    print("Andi tests passed.")

    print("\nAll incentive logic tests completed successfully!")

def create_item(item_code="Item 1"):
    if not frappe.db.exists("Item", item_code):
        item_doc = frappe.new_doc("Item")
        item_doc.item_code = item_code
        item_doc.item_name = item_code
        item_doc.item_group = "All Item Groups"
        item_doc.is_stock_item = 0
        item_doc.insert(ignore_permissions=True)
        frappe.db.commit() # Commit after item creation

# Main execution
if __name__ == "__main__":
    frappe.set_user("Administrator") # Ensure operations run with admin privileges
    try:
        frappe.db.begin() # Start a new transaction
        cleanup_dummy_data() # Ensure clean slate before setup
        setup_dummy_data()
        run_tests()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error during test execution")
        print(f"\nTEST FAILED: {e}")
        frappe.db.rollback() # Rollback on error
    else:
        frappe.db.commit() # Commit only if all tests pass
    finally:
        print("Test execution finished. Data might be left in DB for inspection if tests failed.")
        # To clean up data even if tests pass, uncomment cleanup_dummy_data()
        # cleanup_dummy_data()
