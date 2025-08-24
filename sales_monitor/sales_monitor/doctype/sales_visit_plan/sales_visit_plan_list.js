frappe.listview_settings['Sales Visit Plan'] = {
    add_fields: ["planned_visit_date", "employee_name", "status", "planned_visit_count"],
    get_indicator: function(doc) {
        if (doc.status === "Planned") {
            return [__("Planned"), "blue", "status,=,Planned"];
        } else if (doc.status === "Completed") {
            return [__("Completed"), "green", "status,=,Completed"];
        } else if (doc.status === "Cancelled") {
            return [__("Cancelled"), "red", "status,=,Cancelled"];
        } else if (doc.status === "Draft") {
            return [__("Draft"), "orange", "status,=,Draft"];
        }
        return [__("Draft"), "darkgrey"];
    },
    onload: function(listview) {
        // Listen for real-time updates for Sales Visit Plan
        frappe.realtime.on('doc_update', function(data) {
            if (data.doctype === 'Sales Visit Plan' || data.doctype === 'Sales Visit Plan Item') {
                listview.refresh();
            }
        });

        frappe.realtime.on('doc_submit', function(data) {
            if (data.doctype === 'Sales Visit Plan' || data.doctype === 'Sales Visit Plan Item') {
                listview.refresh();
            }
        });

        frappe.realtime.on('doc_cancel', function(data) {
            if (data.doctype === 'Sales Visit Plan' || data.doctype === 'Sales Visit Plan Item') {
                listview.refresh();
            }
        });
    }
};