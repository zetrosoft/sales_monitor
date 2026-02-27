from frappe.utils import getdate, get_month, get_year
import frappe

def get_sales_incentive_amount(employee, start_date, end_date):
    """
    Fungsi ini akan dipanggil dari Salary Structure untuk mendapatkan
    jumlah Sales Incentive untuk seorang karyawan dalam periode payroll tertentu.
    """
    if not employee or not start_date or not end_date:
        return 0

    # Ubah tanggal menjadi format bulan dan tahun yang digunakan di Sales Incentive Payment
    month_name = get_month(start_date, as_str=True) # e.g., "January"
    year = get_year(start_date)

    # Konversi nama bulan Inggris ke Indonesia agar sesuai dengan DocType
    month_map = {
        "January": "Januari", "February": "Februari", "March": "Maret", "April": "April",
        "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus",
        "September": "September", "October": "Oktober", "November": "November", "December": "Desember"
    }
    month_indonesian = month_map.get(month_name)

    if not month_indonesian:
        frappe.log_error(f"Nama bulan {month_name} tidak ditemukan di map konversi.", "Sales Incentive Payroll Error")
        return 0

    # Cari Sales Person yang terkait dengan Employee ini
    sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
    if not sales_person:
        frappe.log_error(f"Sales Person tidak ditemukan untuk Employee: {employee}", "Sales Incentive Payroll Error")
        return 0

    # Cari Sales Incentive Payment yang sudah disubmit untuk Sales Person dan periode ini
    incentive_doc_name = frappe.db.get_value(
        "Sales Incentive Payment",
        filters={
            "sales_person": sales_person,
            "month": month_indonesian,
            "year": str(year), # Tahun disimpan sebagai string di DocType
            "docstatus": 1 # Hanya dokumen yang disubmit
        },
        fieldname="name"
    )

    if incentive_doc_name:
        incentive_doc = frappe.get_doc("Sales Incentive Payment", incentive_doc_name)
        return incentive_doc.grand_total
    else:
        # Jika tidak ada dokumen insentif yang disubmit untuk periode ini, kembalikan 0
        return 0

