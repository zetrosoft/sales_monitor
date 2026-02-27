frappe.query_reports["Sales Incentive Detail"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": __("Bulan"),
			"fieldtype": "Select",
			"options": "
Januari
Februari
Maret
April
Mei
Juni
Juli
Agustus
September
Oktober
November
Desember",
			"default": frappe.datetime.now_datetime().split('-')[1],
			"reqd": 1
		},
		{
			"fieldname": "year",
			"label": __("Tahun"),
			"fieldtype": "Int",
			"default": frappe.datetime.now_datetime().split('-')[0],
			"reqd": 1
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person",
			"reqd": 1 // Sales person is required for detail report
		}
	]
};
