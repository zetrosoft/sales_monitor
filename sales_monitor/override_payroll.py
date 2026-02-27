import frappe
from frappe.utils import getdate, get_first_day, get_last_day
from frappe import _
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry

# Monkey Patching SalarySlip.check_existing
original_salary_slip_check_existing = SalarySlip.check_existing

def patched_salary_slip_check_existing(self):
    # Jika slip ini ditandai sebagai insentif, lewati pengecekan duplikasi standar
    if getattr(self, "custom_is_incentive_slip", None) or (self.payroll_entry and frappe.db.get_value("Payroll Entry", self.payroll_entry, "custom_incentive_employee_incentive")):
        return
    return original_salary_slip_check_existing(self)

SalarySlip.check_existing = patched_salary_slip_check_existing

# Monkey Patching PayrollEntry.validate_existing_salary_slips
original_payroll_entry_validate_existing = PayrollEntry.validate_existing_salary_slips

def patched_payroll_entry_validate_existing(self):
    # Jika Payroll Entry ini adalah untuk insentif, lewati validasi slip gaji yang sudah ada
    if getattr(self, "custom_incentive_employee_incentive", None):
        return
    return original_payroll_entry_validate_existing(self)

PayrollEntry.validate_existing_salary_slips = patched_payroll_entry_validate_existing

@frappe.whitelist()
def get_existing_incentive_payroll_entry(employee_incentive_name):
    """Cek apakah Payroll Entry untuk Employee Incentive ini sudah ada."""
    pe = frappe.db.get_value("Payroll Entry", {"custom_incentive_employee_incentive": employee_incentive_name}, "name")
    return pe

@frappe.whitelist()
def create_incentive_payroll_entry(employee_incentive_name):
    """Buat Payroll Entry khusus untuk Insentif ini."""
    ei = frappe.get_doc("Employee Incentive", employee_incentive_name)
    
    # Buat Payroll Entry Baru
    pe = frappe.new_doc("Payroll Entry")
    pe.payroll_frequency = "Monthly"
    pe.posting_date = getdate()
    pe.start_date = get_first_day(ei.payroll_date)
    pe.end_date = get_last_day(ei.payroll_date)
    pe.company = ei.company
    pe.currency = ei.currency or "IDR"
    pe.exchange_rate = 1.0
    pe.payroll_payable_account = frappe.db.get_value("Company", ei.company, "default_payroll_payable_account")
    pe.cost_center = frappe.db.get_value("Company", ei.company, "cost_center")
    
    # Filter karyawan agar hanya untuk si penerima insentif
    pe.append("employees", {
        "employee": ei.employee,
        "employee_name": ei.employee_name
    })
    
    # Simpan nama Employee Incentive di field kustom agar bisa dilacak dan di-filter
    pe.custom_incentive_employee_incentive = employee_incentive_name
    
    pe.insert()
    pe.submit() # Otomatis submit agar bisa langsung diproses
    
    # Update dokumen Employee Incentive dengan link ke Payroll Entry ini
    ei.db_set("custom_incentive_payroll_entry", pe.name)
    
    return pe.name

# Method override untuk perhitungan Salary Slip
def calculate_net_pay_override(salary_slip_doc):
    """
    Override logika calculate_net_pay di Salary Slip.
    Jika ini adalah Payroll Entry Insentif, hanya komponen "Tj. Lain" yang diisi.
    """
    pe_name = salary_slip_doc.payroll_entry
    if not pe_name:
        return SalarySlip.calculate_net_pay(salary_slip_doc)

    pe = frappe.get_doc("Payroll Entry", pe_name)

    if getattr(pe, "custom_incentive_employee_incentive", None):
        salary_slip_doc.custom_is_incentive_slip = 1
        
        employee_incentive_name = getattr(pe, "custom_incentive_employee_incentive")
        ei = frappe.get_doc("Employee Incentive", employee_incentive_name)

        # Bersihkan list yang sudah ada
        salary_slip_doc.set("earnings", [])
        salary_slip_doc.set("deductions", [])

        # 1. Tambahkan Komponen Utama: Tj. Lain
        salary_slip_doc.append("earnings", {
            "salary_component": "Tj. Lain",
            "amount": ei.incentive_amount,
            "base_amount": ei.incentive_amount,
            "parentfield": "earnings",
            "parenttype": "Salary Slip",
            "doctype": "Salary Slip Earning",
            "currency": salary_slip_doc.currency or "IDR"
        })
        
        # 2. Ambil semua komponen dari Salary Structure Karyawan dan set nilainya ke 0
        ss_name = salary_slip_doc.salary_structure
        if not ss_name:
            ss_name = frappe.db.get_value("Salary Structure Assignment", 
                {"employee": salary_slip_doc.employee, "docstatus": 1}, "salary_structure")
        
        if ss_name:
            ss = frappe.get_doc("Salary Structure", ss_name)
            
            # Loop Earnings dari Structure
            for item in ss.earnings:
                if item.salary_component != "Tj. Lain":
                    salary_slip_doc.append("earnings", {
                        "salary_component": item.salary_component,
                        "amount": 0,
                        "base_amount": 0,
                        "parentfield": "earnings",
                        "parenttype": "Salary Slip",
                        "doctype": "Salary Slip Earning",
                        "currency": salary_slip_doc.currency
                    })
            
            # Loop Deductions dari Structure
            for item in ss.deductions:
                salary_slip_doc.append("deductions", {
                    "salary_component": item.salary_component,
                    "amount": 0,
                    "base_amount": 0,
                    "parentfield": "deductions",
                    "parenttype": "Salary Slip",
                    "doctype": "Salary Slip Deduction",
                    "currency": salary_slip_doc.currency
                })

        # 3. Hitung Total Gaji (Hanya dari Tj. Lain)
        salary_slip_doc.gross_pay = ei.incentive_amount
        salary_slip_doc.base_gross_pay = ei.incentive_amount
        salary_slip_doc.net_pay = ei.incentive_amount
        salary_slip_doc.base_net_pay = ei.incentive_amount
        salary_slip_doc.total_deduction = 0
        salary_slip_doc.base_total_deduction = 0
        salary_slip_doc.rounded_total = ei.incentive_amount
        salary_slip_doc.base_rounded_total = ei.incentive_amount

    else:
        # Jika bukan Payroll Entry Insentif, panggil metode asli dari kelas
        return SalarySlip.calculate_net_pay(salary_slip_doc)
