import frappe
from frappe import _
from sales_monitor.api import get_net_turnover, get_join_new_bonus, get_incentive_tier
from frappe.utils import getdate, get_first_day, get_last_day

def execute(filters=None):
    if not filters.get("sales_person"):
        frappe.throw(_("Sales Person is required for Sales Incentive Detail Report."))

    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Tipe"), "fieldname": "type", "fieldtype": "Data", "width": 120},
        {"label": _("Nama Dokumen"), "fieldname": "document_name", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": _("Tanggal"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Pelanggan"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": _("Nilai Transaksi"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Keterangan"), "fieldname": "remark", "fieldtype": "Small Text", "width": 200},
        {"label": _("Bonus"), "fieldname": "bonus_amount", "fieldtype": "Currency", "width": 100}
    ]

def get_data(filters):
    month_map = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    
    month_num = month_map.get(filters.get("month"))
    year = filters.get("year")
    sales_person = filters.get("sales_person")
    
    if not month_num or not year or not sales_person:
        return []
        
    start_date = get_first_day(f"{year}-{month_num}-01")
    end_date = get_last_day(f"{year}-{month_num}-01")
    
    report_data = []

    # 1. Determine Sales Person's incentive category and applicable settings
    employee = frappe.db.get_value("Employee", {"sales_person": sales_person}, "name")
    user_id = frappe.db.get_value("Employee", employee, "user_id") if employee else None
    if not user_id:
        frappe.throw(_(f"No user found for Sales Person {sales_person}. Cannot determine applicable roles."))
    user_roles = frappe.get_roles(user_id)

    incentive_setting_docs = frappe.get_all(
        "Sales Incentive Setting",
        filters=[
            ["applies_to_role", "in", user_roles],
            ["valid_from", "<=", end_date],
            ["valid_until", ">=", start_date]
        ],
        fields=["name", "incentive_category"],
        order_by="valid_from desc",
        limit=1
    )
    
    if not incentive_setting_docs:
        frappe.throw(_(f"No active Sales Incentive Setting found for Sales Person {sales_person} in {filters.get('month')} {year}."))

    setting_name = incentive_setting_docs[0].name
    incentive_category = incentive_setting_docs[0].incentive_category
    setting_doc = frappe.get_doc("Sales Incentive Setting", setting_name)

    customer_group_filters_list = []
    if incentive_category == "SPV Sales" and setting_doc.customer_group_filter:
        customer_group_filters_list = [g.customer_group for g in setting_doc.customer_group_filter]


    # --- SECTION: DETAIL OMSET ---
    report_data.append({"type": "HEADER", "document_name": _("DETAIL OMSET"), "amount": ""})

    # Get all sales invoices for the period
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "sales_person": sales_person,
            "posting_date": ["between", [start_date, end_date]],
            "docstatus": 1,
            "is_return": 0
        },
        fields=["name", "posting_date", "customer", "grand_total"],
        order_by="posting_date asc"
    )

    total_sales_for_period = 0
    for inv in sales_invoices:
        customer_group = frappe.db.get_value("Customer", inv.customer, "customer_group")
        is_relevant = True
        if incentive_category == "SPV Sales" and customer_group_filters_list:
            if customer_group not in customer_group_filters_list:
                is_relevant = False
        
        if is_relevant:
            report_data.append({
                "type": "Sales",
                "document_name": inv.name,
                "date": inv.posting_date,
                "customer": inv.customer,
                "amount": inv.grand_total,
                "remark": f"Omset Penjualan (Grup: {customer_group})"
            })
            total_sales_for_period += inv.grand_total

    # Get all sales returns for the period
    sales_returns = frappe.get_all(
        "Sales Invoice",
        filters={
            "sales_person": sales_person,
            "posting_date": ["between", [start_date, end_date]],
            "docstatus": 1,
            "is_return": 1
        },
        fields=["name", "posting_date", "customer", "grand_total"],
        order_by="posting_date asc"
    )
    total_returns_for_period = 0
    for ret in sales_returns:
        customer_group = frappe.db.get_value("Customer", ret.customer, "customer_group")
        is_relevant = True
        if incentive_category == "SPV Sales" and customer_group_filters_list:
            if customer_group not in customer_group_filters_list:
                is_relevant = False

        if is_relevant:
            report_data.append({
                "type": "Return",
                "document_name": ret.name,
                "date": ret.posting_date,
                "customer": ret.customer,
                "amount": -ret.grand_total, # Show as negative
                "remark": f"Retur Penjualan (Grup: {customer_group})"
            })
            total_returns_for_period += ret.grand_total

    # Calculate Net Turnover (re-use the api function for consistency, but we have the breakdown)
    net_turnover = get_net_turnover(sales_person, start_date, end_date, incentive_category, frappe.json.dumps(customer_group_filters_list))
    
    report_data.append({
        "type": "Total", "document_name": _("TOTAL OMSET BERSIH"), 
        "amount": net_turnover, "bold": True
    })
    
    # --- SECTION: DETAIL BONUS PELANGGAN BARU ---
    report_data.append({"type": "HEADER", "document_name": _("DETAIL BONUS PELANGGAN BARU"), "amount": ""})

    join_new_data = get_join_new_bonus(sales_person, start_date, end_date)
    total_join_new_bonus = join_new_data["total_bonus"]

    if join_new_data["details"]:
        for detail in join_new_data["details"]:
            report_data.append({
                "type": "Join New",
                "document_name": detail["first_invoice"],
                "date": detail["first_invoice_date"],
                "customer": detail["customer"],
                "amount": detail["first_order_value"],
                "remark": detail["bonus_keterangan"],
                "bonus_amount": detail["bonus_amount"]
            })
    else:
        report_data.append({"type": "Join New", "remark": _("Tidak ada bonus pelanggan baru."), "bonus_amount": 0.0})

    report_data.append({
        "type": "Total", "document_name": _("TOTAL BONUS PELANGGAN BARU"), 
        "bonus_amount": total_join_new_bonus, "bold": True
    })

    # --- SECTION: RINGKASAN BONUS OMSET ---
    report_data.append({"type": "HEADER", "document_name": _("RINGKASAN BONUS OMSET"), "amount": ""})

    tier_info = get_incentive_tier(net_turnover, sales_person, start_date)
    bonus_omset_from_tier = 0.0
    bonus_admin_from_tier = 0.0

    if tier_info:
        bonus_omset_from_tier = net_turnover * tier_info["persentase"]
        bonus_admin_from_tier = tier_info["bonus_admin"]
        report_data.append({
            "type": "Ringkasan", "document_name": _("Omset Tercapai"),
            "remark": f"Rp {net_turnover:,.2f} (Target Min: Rp {tier_info['min_omset']:,.2f})",
            "amount": net_turnover
        })
        report_data.append({
            "type": "Ringkasan", "document_name": _("Persentase Bonus"),
            "remark": f"{tier_info['persentase'] * 100:.2f}% dari omset",
            "bonus_amount": bonus_omset_from_tier
        })
        report_data.append({
            "type": "Ringkasan", "document_name": _("Bonus Admin Tetap"),
            "bonus_amount": bonus_admin_from_tier
        })
    else:
        report_data.append({"type": "Ringkasan", "remark": _("Tidak ada tier omset yang tercapai."), "bonus_amount": 0.0})
    
    report_data.append({
        "type": "Total", "document_name": _("TOTAL BONUS OMSET"),
        "bonus_amount": bonus_omset_from_tier + bonus_admin_from_tier, "bold": True
    })

    # --- SECTION: GRAND SUMMARY ---
    report_data.append({"type": "HEADER", "document_name": _("GRAND TOTAL INSENTIF"), "amount": ""})
    grand_total_incentive = total_join_new_bonus + bonus_omset_from_tier + bonus_admin_from_tier
    report_data.append({
        "type": "GRAND TOTAL", "document_name": _("TOTAL INSENTIF BULAN INI"),
        "bonus_amount": grand_total_incentive, "bold": True
    })

    return report_data
