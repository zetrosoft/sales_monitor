import frappe
from frappe.utils import getdate, get_first_day, get_last_day, flt
from frappe import _
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry

# Monkey Patching SalarySlip.check_existing
original_salary_slip_check_existing = SalarySlip.check_existing

def patched_salary_slip_check_existing(self):
    # Jika slip ini ditandai sebagai insentif atau berasal dari Payroll Entry insentif, lewati pengecekan duplikasi
    is_incentive = getattr(self, "custom_is_incentive_slip", None)
    if not is_incentive and self.payroll_entry:
        is_incentive = frappe.db.get_value("Payroll Entry", self.payroll_entry, "custom_incentive_employee_incentive")
    
    if is_incentive:
        return # Skip standard check
    
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

# Monkey Patching SalarySlip.calculate_net_pay
original_calculate_net_pay = SalarySlip.calculate_net_pay

def patched_calculate_net_pay(self, skip_tax_breakup_computation: bool = False):
    pe_name = self.payroll_entry
    if not pe_name:
        return original_calculate_net_pay(self, skip_tax_breakup_computation)

    # Cek apakah Payroll Entry ini memiliki link ke Employee Incentive
    custom_incentive = frappe.db.get_value("Payroll Entry", pe_name, "custom_incentive_employee_incentive")

    if custom_incentive:
        self.custom_is_incentive_slip = 1
        
        ei = frappe.get_doc("Employee Incentive", custom_incentive)
        target_component = ei.salary_component or "Tj. Lain"

        # Bersihkan list yang sudah ada
        self.set("earnings", [])
        self.set("deductions", [])

        # 1. Cari Salary Structure
        ss_name = self.salary_structure
        if not ss_name:
            ss_name = frappe.db.get_value("Salary Structure Assignment", 
                {"employee": self.employee, "docstatus": 1, "from_date": ["<=", self.end_date or getdate()]}, 
                "salary_structure", order_by="from_date desc")
        
        if ss_name:
            ss = frappe.get_doc("Salary Structure", ss_name)
            
            # 2. Loop Earnings dari Structure (Menjaga Urutan Asli)
            target_component_found = False
            for item in ss.earnings:
                amount = 0.0
                if item.salary_component == target_component:
                    amount = flt(ei.incentive_amount)
                    target_component_found = True
                
                self.append("earnings", {
                    "salary_component": item.salary_component,
                    "amount": amount,
                    "base_amount": amount,
                    "default_amount": 0.0
                })
            
            # 3. Jika target_component tidak ada di Salary Structure, tambahkan di paling bawah
            if not target_component_found:
                 self.append("earnings", {
                    "salary_component": target_component,
                    "amount": flt(ei.incentive_amount),
                    "base_amount": flt(ei.incentive_amount),
                    "default_amount": 0.0
                })
            
            # 4. Loop Deductions dari Structure (Semua set ke 0)
            for item in ss.deductions:
                self.append("deductions", {
                    "salary_component": item.salary_component,
                    "amount": 0.0,
                    "base_amount": 0.0,
                    "default_amount": 0.0
                })
        else:
            # Fallback jika tidak ada Salary Structure sama sekali
            self.append("earnings", {
                "salary_component": target_component,
                "amount": flt(ei.incentive_amount),
                "base_amount": flt(ei.incentive_amount),
                "default_amount": 0.0
            })

        # 3. Hitung Total Gaji
        amount_val = flt(ei.incentive_amount)
        self.gross_pay = amount_val
        self.base_gross_pay = amount_val
        self.net_pay = amount_val
        self.base_net_pay = amount_val
        self.total_deduction = 0.0
        self.base_total_deduction = 0.0
        self.rounded_total = amount_val
        self.base_rounded_total = amount_val
        
        self.flags.calculated = True
        return 
    else:
        return original_calculate_net_pay(self, skip_tax_breakup_computation)

SalarySlip.calculate_net_pay = patched_calculate_net_pay

@frappe.whitelist()
def emergency_break_link(incentive_name, payroll_name):
    """Fungsi darurat untuk melepas kuncian antara Employee Incentive dan Payroll Entry."""
    frappe.db.set_value("Employee Incentive", incentive_name, "custom_incentive_payroll_entry", None)
    frappe.db.set_value("Payroll Entry", payroll_name, "custom_incentive_employee_incentive", None)
    frappe.db.commit()
    return "Kuncian berhasil dilepas. Silakan coba hapus Payroll Entry sekarang."

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
    
    # Update dokumen Employee Incentive dengan link ke Payroll Entry ini
    ei.db_set("custom_incentive_payroll_entry", pe.name)
    
    return pe.name
