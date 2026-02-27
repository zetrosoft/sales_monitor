import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_first_day, get_last_day
from frappe import _

from sales_monitor.api import get_net_turnover, get_join_new_bonus, get_incentive_tier

class SalesIncentivePayment(Document):
    def autoname(self):
        if not self.sales_person:
            frappe.throw(_("Sales Person harus dipilih."))
        
        self.name = f"{self.month}-{self.year}-{self.sales_person}"

    def on_submit(self):
        # Pastikan dokumen Sales Incentive Payment sudah disubmit
        if self.docstatus != 1:
            frappe.throw(_("Sales Incentive Payment harus disubmit terlebih dahulu."))
            
        # Dapatkan Employee dari Sales Person
        employee_id = frappe.db.get_value("Sales Person", self.sales_person, "employee")
        if not employee_id:
            frappe.throw(_(f"Employee tidak ditemukan untuk Sales Person: {self.sales_person}"))
            
        # Tentukan tanggal payroll (akhir bulan)
        month_map = {
            "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
            "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
            "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
        }
        month_num = month_map.get(self.month)
        if not month_num:
            frappe.throw(_(f"Bulan '{self.month}' tidak valid."))

        payroll_date = frappe.utils.get_last_day(f"{self.year}-{month_num}-01")
        
        # Cek apakah sudah ada Employee Incentive yang dibuat dari dokumen ini
        existing_incentive = frappe.db.get_value(
            "Employee Incentive",
            {"custom_sales_incentive_payment_ref": self.name}, # Perbaikan di sini
            "name"
        )
        
        if existing_incentive:
            frappe.msgprint(_(f"Employee Incentive {existing_incentive} sudah dibuat untuk dokumen ini."))
            return

        # Buat dokumen Employee Incentive baru
        try:
            ei = frappe.new_doc("Employee Incentive")
            ei.employee = employee_id
            ei.payroll_date = payroll_date
            ei.incentive_amount = self.grand_total
            ei.salary_component = "Tj. Lain" # Menggunakan nama komponen gaji yang benar sesuai konfirmasi
            ei.status = "Draft" # Sesuai permintaan
            setattr(ei, "custom_sales_incentive_payment_ref", self.name) # Perbaikan di sini
            ei.insert(ignore_permissions=True)

            frappe.msgprint(_(f"Employee Incentive {ei.name} berhasil dibuat dengan status Draft."))
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), _("Gagal membuat Employee Incentive dari Sales Incentive Payment"))
            frappe.throw(_(f"Gagal membuat Employee Incentive: {e}"))


    def before_save(self):
        self.grand_total = sum(d.total_bonus for d in self.incentive_items)

@frappe.whitelist()
def sales_person_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT sp.name, emp.employee_name as description
        FROM `tabSales Person` sp
        JOIN `tabEmployee` emp ON sp.employee = emp.name
        WHERE sp.employee IS NOT NULL AND (sp.name LIKE %(txt)s OR emp.employee_name LIKE %(txt)s)
        ORDER BY sp.name LIMIT %(page_len)s OFFSET %(start)s
    """, {"txt": f"%{txt}%", "page_len": page_len, "start": start}, as_list=1)

@frappe.whitelist()
def process_sales_incentive(month, year, sales_person_name=None):
    try:
        month_map = {
            "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
            "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
            "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
        }
        month_num = month_map.get(month)
        start_date = get_first_day(f"{year}-{month_num}-01")
        end_date = get_last_day(f"{year}-{month_num}-01")

        if not sales_person_name:
            frappe.throw(_("Sales Person harus dipilih."))

        # 1. Identity Context (Fixed to Sales User Role context as requested)
        applied_role = "Sales User"
        setting_info = frappe.get_all("Sales Incentive Setting", 
            filters=[["applies_to_role", "=", applied_role], ["valid_from", "<=", end_date]],
            fields=["name", "incentive_category"], order_by="valid_from desc", limit=1)
        
        if not setting_info:
            frappe.throw(_(f"Tidak ada setting untuk role {applied_role} pada periode {month} {year}"))

        setting_doc = frappe.get_doc("Sales Incentive Setting", setting_info[0].name)
        groups = [g.customer_group for g in setting_doc.customer_group_filter] if setting_info[0].incentive_category == "SPV Sales" else []

        # 2. Base Calculations
        net_turnover = get_net_turnover(sales_person_name, start_date, end_date, setting_info[0].incentive_category, frappe.json.dumps(groups))
        join_new_result = get_join_new_bonus(sales_person_name, start_date, end_date)
        tier_info = get_incentive_tier(net_turnover, sales_person_name, start_date)

        details = []

        # 3. Baris 1: Omset Penjualan
        bonus_omset = net_turnover * tier_info.get("persentase", 0) if tier_info else 0
        bonus_admin_tier = tier_info.get("bonus_admin", 0) if tier_info else 0
        
        details.append({
            "tipe_incentive": "Omset Penjualan",
            "total_omset": net_turnover,
            "jumlah": 1,
            "percentage": tier_info.get("persentase", 0) * 100 if tier_info else 0,
            "bonus_omset": bonus_omset,
            "bonus_admin": bonus_admin_tier,
            "total_bonus": bonus_omset + bonus_admin_tier
        })

        # 4. Baris Selanjutnya: Breakdown Join New
        # Kita ambil dari detail setting agar baris tetap muncul walau 0
        for rule in setting_doc.bonus_join_new_table:
            # Cari di hasil kalkulasi yang labelnya cocok
            matching_details = [d for d in join_new_result["details"] if d['label'] == rule.keterangan]
            
            sub_total_omset = sum(d['amount'] for d in matching_details)
            count = len(matching_details)
            
            details.append({
                "tipe_incentive": f"Join New ({rule.keterangan})",
                "total_omset": sub_total_omset,
                "jumlah": count,
                "percentage": 0,
                "bonus_omset": 0,
                "bonus_admin": rule.bonus,
                "total_bonus": count * rule.bonus
            })

        return {
            "applied_role": applied_role,
            "active_scheme": setting_doc.name,
            "grand_total": sum(d['total_bonus'] for d in details),
            "details": details
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "process_sales_incentive_error")
        frappe.throw(_(f"Gagal memproses insentif: {str(e)}"))
