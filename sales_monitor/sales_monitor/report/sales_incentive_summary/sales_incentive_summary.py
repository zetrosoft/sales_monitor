import frappe
from frappe import _
from sales_monitor.api import get_net_turnover, get_join_new_bonus, get_incentive_tier
from frappe.utils import getdate, get_first_day, get_last_day

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Link", "options": "Sales Person", "width": 200},
        {"label": _("Kategori"), "fieldname": "category", "fieldtype": "Data", "width": 120},
        {"label": _("Omset Bersih"), "fieldname": "net_turnover", "fieldtype": "Currency", "width": 150},
        {"label": _("Tier %"), "fieldname": "tier_percentage", "fieldtype": "Percent", "width": 100},
        {"label": _("Bonus Omset"), "fieldname": "bonus_omset", "fieldtype": "Currency", "width": 130},
        {"label": _("Bonus Join New"), "fieldname": "bonus_join_new", "fieldtype": "Currency", "width": 130},
        {"label": _("Bonus Admin"), "fieldname": "bonus_admin", "fieldtype": "Currency", "width": 130},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 150}
    ]

def get_data(filters):
    month_map = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    
    month_num = month_map.get(filters.get("month"))
    year = filters.get("year")
    
    if not month_num or not year:
        return []
        
    start_date = f"{year}-{month_num}-01"
    end_date = get_last_day(start_date)
    
    sales_persons = []
    if filters.get("sales_person"):
        sales_persons = [filters.get("sales_person")]
    else:
        sales_persons = frappe.get_all("Sales Person", filters={"enabled": 1}, pluck="name")
        
    data = []
    
    for sp in sales_persons:
        # 1. Get Employee & Category
        employee = frappe.db.get_value("Employee", {"sales_person": sp}, "name")
        if not employee: continue
        
        user_id = frappe.db.get_value("Employee", employee, "user_id")
        if not user_id: continue
        
        roles = frappe.get_roles(user_id)
        
        # Determine category based on setting
        setting_info = frappe.get_all(
            "Sales Incentive Setting",
            filters=[["applies_to_role", "in", roles], ["valid_from", "<=", start_date]],
            fields=["name", "incentive_category"],
            order_by="valid_from desc",
            limit=1
        )
        
        if not setting_info: continue
        
        category = setting_info[0].incentive_category
        setting_doc = frappe.get_doc("Sales Incentive Setting", setting_info[0].name)
        
        # customer group filter for SPV
        groups = [g.customer_group for g in setting_doc.customer_group_filter] if category == "SPV Sales" else []
        
        # 2. Calculate Net Turnover
        net_turnover = get_net_turnover(sp, start_date, end_date, category, groups)
        
        # 3. Match Tier
        tier = get_incentive_tier(net_turnover, sp, start_date)
        
        # 4. Join New Bonus
        join_new = get_join_new_bonus(sp, start_date, end_date)
        
        bonus_omset = (net_turnover * tier["persentase"]) if tier else 0.0
        bonus_admin = tier["bonus_admin"] if tier else 0.0
        bonus_join_new = join_new["total_bonus"]
        
        grand_total = bonus_omset + bonus_admin + bonus_join_new
        
        if grand_total > 0 or net_turnover > 0:
            data.append({
                "sales_person": sp,
                "category": category,
                "net_turnover": net_turnover,
                "tier_percentage": (tier["persentase"] * 100) if tier else 0,
                "bonus_omset": bonus_omset,
                "bonus_join_new": bonus_join_new,
                "bonus_admin": bonus_admin,
                "grand_total": grand_total
            })
            
    return data
