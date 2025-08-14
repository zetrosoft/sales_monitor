frappe.listview_settings['Sales Activity Monitoring'] = {
    add_fields: ["plan_date_time", "checkin_time", "checkout_time", "duration", "notes", "map_link", "image_link", "status"],
    get_indicator: function(doc) {
        if (doc.status === "Completed") {
            return [__("Completed"), "green", "status,=,Completed"];
        } else if (doc.status === "Checked In") {
            return [__("Checked In"), "blue", "status,=,Checked In"];
        } else if (doc.status === "Planned") {
            return [__("Planned"), "orange", "status,=,Planned"];
        } else if (doc.status === "Cancelled") {
            return [__("Cancelled"), "red", "status,=,Cancelled"];
        }
        return [__("Draft"), "darkgrey"];
    }
};