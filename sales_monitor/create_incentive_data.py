import frappe

def create_sales_incentive_data():
    # --- Pastikan Customer Group yang dibutuhkan ada ---
    customer_groups = ["Distributor"]
    for group in customer_groups:
        if not frappe.db.exists("Customer Group", group):
            frappe.get_doc({"doctype": "Customer Group", "customer_group_name": group}).insert()
            
    # --- DATA 1: Bonus Admin Sales ---
    title1 = "Bonus Admin Sales 2026"
    if frappe.db.exists("Sales Incentive Setting", title1):
        frappe.delete_doc("Sales Incentive Setting", title1)
    
    doc1 = frappe.get_doc({
        "doctype": "Sales Incentive Setting",
        "title": title1,
        "incentive_category": "Admin Sales",
        "applies_to_role": "Sales User",
        "valid_from": "2026-01-01",
        "description": "Perhitungan Omset dari seluruh penjualan/barang terfaktur setiap bulannya (setelah dikurangi return bulan berjalan). Bonus akan dihitung dan dibayar minggu ke-2 setiap bulannya setelah closing.",
        # customer_group_filter dikosongkan karena ini untuk semua grup
        "bonus_join_new_table": [
            {"keterangan": "Join Reseller", "order_awal": 500000, "bonus": 5000},
            {"keterangan": "Join Agen", "order_awal": 10000000, "bonus": 50000},
            {"keterangan": "Join Agen -> Distributor", "order_awal": 100000000, "bonus": 250000}
        ],
        "bonus_penjualan_table": [
            {"omset_bulanan_min": 1800000000, "bonus_admin": 50000, "persentase": 0.003},
            {"omset_bulanan_min": 2000000000, "bonus_admin": 100000, "persentase": 0.005},
            {"omset_bulanan_min": 2500000000, "bonus_admin": 150000, "persentase": 0.006},
            {"omset_bulanan_min": 3000000000, "bonus_admin": 200000, "persentase": 0.007},
            {"omset_bulanan_min": 4000000000, "bonus_admin": 300000, "persentase": 0.008},
            {"omset_bulanan_min": 5000000000, "bonus_admin": 500000, "persentase": 0.010}
        ]
    })
    doc1.insert()

    # --- DATA 2: Bonus SPV Sales ---
    title2 = "Bonus SPV Sales 2026"
    if frappe.db.exists("Sales Incentive Setting", title2):
        frappe.delete_doc("Sales Incentive Setting", title2)
    
    doc2 = frappe.get_doc({
        "doctype": "Sales Incentive Setting",
        "title": title2,
        "incentive_category": "SPV Sales",
        "applies_to_role": "Sales Manager",
        "valid_from": "2026-01-01",
        "description": "Perhitungan Omset hanya dari total penjualan pelanggan 'Distributor'.",
        "customer_group_filter": [
            {"customer_group": "Distributor"}
        ],
        "bonus_join_new_table": [
            {"keterangan": "Join Distributor", "order_awal": 100000000, "bonus": 500000},
            {"keterangan": "Join Agen -> Distributor", "order_awal": 100000000, "bonus": 250000}
        ],
        "bonus_penjualan_table": [
            {"omset_bulanan_min": 1500000000, "bonus_admin": 300000, "persentase": 0.02},
            {"omset_bulanan_min": 2000000000, "bonus_admin": 500000, "persentase": 0.03},
            {"omset_bulanan_min": 2500000000, "bonus_admin": 1000000, "persentase": 0.04},
            {"omset_bulanan_min": 3000000000, "bonus_admin": 2000000, "persentase": 0.07},
            {"omset_bulanan_min": 4000000000, "bonus_admin": 3000000, "persentase": 0.08},
            {"omset_bulanan_min": 5000000000, "bonus_admin": 5000000, "persentase": 0.10}
        ]
    })
    doc2.insert()

    frappe.db.commit()
    print(f"Successfully created/updated Sales Incentive Settings: '{title1}' and '{title2}' with new structure.")

# Jalankan fungsi ini dari bench console: `bench --site [nama_site] execute frappe-bench.apps.sales_monitor.sales_monitor.create_incentive_data.create_sales_incentive_data`
if __name__ == "__main__":
    create_sales_incentive_data()
