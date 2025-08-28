// Copyright (c) 2024, a and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Activity Monitoring"] = {
    "filters": [
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "Employee"
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "date_range",
            "label": __("Date Range"),
            "fieldtype": "DateRange",
            "default": [frappe.datetime.add_months(frappe.datetime.now_date(), -1), frappe.datetime.now_date()]
        }
    ],
    "formatter": function(value, row, column, data) {
        console.log("Formatter called for column:", column.id, "Value:", value, "Row data:", data);

        if (column.id === "customer" && data.customer_address) {
            console.log("Customer address found:", data.customer_address);
            return `<span title="${data.customer_address}">${value}</span>`;
        }

        if (column.id === "photo" && data.photo) {
            console.log("Photo data found:", data.photo);
            return `<a href="${data.photo}" target="_blank">
                <img src="${data.photo}" style="max-width: 50px; max-height: 50px;" alt="Visit Photo">
            </a>`;
        }
        
        if (column.id === "map_location" && data.latitude && data.longitude) {
            console.log("Map data found: Lat", data.latitude, "Long", data.longitude);
            let url = `https://www.google.com/maps/search/?api=1&query=${data.latitude},${data.longitude}`;
            return `<a href="${url}" target="_blank" title="View on Map">
                <i class="fa fa-map-location" style="font-size: 1.5em;"></i>
            </a>`;
        }

        return value;
    }
};
