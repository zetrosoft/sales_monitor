// Copyright (c) 2026, Siumang and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Person Visit Metric"] = {
	"filters": [
		{
			"fieldname": "date_from",
			"label": __("Date From"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "date_to",
			"label": __("Date To"),
			"fieldtype": "Date",			
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person"
		}
	],
	"onload": function(report) {
		// Set default date_to to 30 days after date_from, and refresh
		report.page.get_field('date_from').df.on_change = () => {
			let date_from = report.get_values().date_from;
			if (date_from) {
				let date_to = frappe.datetime.add_days(date_from, 30);
				report.set_value('date_to', date_to);
			}
			report.refresh(); // Refresh report on date_from change
		};
		// Refresh report on date_to change
		report.page.get_field('date_to').df.on_change = () => {
			report.refresh();
		};
		// Refresh report on sales_person change
		report.page.get_field('sales_person').df.on_change = () => {
			report.refresh();
		};

		// Auto-refresh report on initial load
		report.refresh();
	}
};