frappe.listview_settings['Sales Activity Monitoring'] = {
    add_fields: ["sales_name", "customer", "plan_date_time", "duration_visit", "map_link", "image_link", "status", "checkin_raw", "checkout_raw"],
    get_list_method: "sales_monitor.doctype.sales_activity_monitoring.sales_activity_monitoring.get_list",
    
    // Custom columns for List View
    get_list_fields: function() {
        return [
            "sales_name", // Sales Name
            "customer", // Customer
            "plan_date_time", // Plan Date
            "duration_visit", // Duration
            "map_link", // Map
            "image_link", // Photo
            "status", // Status (tetap ada)
            "checkin_raw", // Hidden field for duration hover
            "checkout_raw" // Hidden field for duration hover
        ];
    },

    formatters: {
        plan_date_time: function(value, fieldname, doc) {
            // Format Plan Visit to dd-mm-yyyy HH:mm
            if (doc.plan_date_time) {
                return frappe.datetime.str_to_user(doc.plan_date_time).split(" ")[0] + " " + frappe.datetime.str_to_user(doc.plan_date_time).split(" ")[1];
            }
            return "";
        },
        duration_visit: function(value, fieldname, doc) {
            // Display duration and on hover show checkin - checkout
            if (doc.duration_visit) {
                let duration_text = doc.duration_visit + " mins";
                let hover_text = "";
                if (doc.checkin_raw && doc.checkout_raw) {
                    hover_text = frappe.datetime.str_to_user(doc.checkin_raw) + " - " + frappe.datetime.str_to_user(doc.checkout_raw);
                }
                // Use frappe.ui.popover for better hover functionality
                return `<span class="duration-popover" data-html="true" data-toggle="popover" data-placement="top" data-content="${hover_text}">${duration_text}</span>`;
            }
            return "";
        },
        map_link: function(value, fieldname, doc) {
            // Display Map Icon with popup on click/focus
            if (doc.map_link) {
                return `<a href="#" onclick="return false;" data-map-link="${doc.map_link}" data-customer="${doc.customer}" class="map-icon"><i class="fa fa-map-marker"></i></a>`;
            }
            return "";
        },
        image_link: function(value, fieldname, doc) {
            // Display Photo thumbnail with popup on click/focus
            if (doc.image_link) {
                return `<a href="#" onclick="return false;" data-image-link="${doc.image_link}" class="image-thumbnail"><img src="${doc.image_link}" style="width: 30px; height: 30px; object-fit: cover; border-radius: 3px;"></a>`;
            }
            return "";
        }
    },

    onload: function(listview) {
        // Initialize popovers for duration
        listview.page.container.on('mouseenter', '.duration-popover', function() {
            $(this).popover('show');
        }).on('mouseleave', '.duration-popover', function() {
            $(this).popover('hide');
        });

        // Handle Map Icon click
        listview.page.container.on('click', '.map-icon', function() {
            let map_link = $(this).data('map-link');
            let customer_name = $(this).data('customer');

            frappe.call({
                method: "sales_monitor.api.get_customer_visit_info",
                args: {
                    customer_name: customer_name
                },
                callback: function(r) {
                    if (r.message) {
                        let customer_info = r.message;
                        let dialog = new frappe.ui.Dialog({
                            title: __('Customer Location'),
                            fields: [
                                {
                                    fieldtype: 'HTML',
                                    fieldname: 'map_html',
                                    options: `<iframe src="${map_link}" width="100%" height="300px" frameborder="0" style="border:0" allowfullscreen></iframe>`
                                },
                                {
                                    fieldtype: 'HTML',
                                    fieldname: 'info_html',
                                    options: `
                                        <p><strong>${__("Customer")}:</strong> ${customer_info.customer_name}</p>
                                        <p><strong>${__("Address")}:</strong> ${customer_info.address}</p>
                                        <p><strong>${__("Visits Last Year")}:</strong> ${customer_info.visit_count_last_year}</p>
                                    `
                                }
                            ],
                            size: 'small',
                            primary_action_label: __('Close'),
                            primary_action: function() {
                                dialog.hide();
                            }
                        });
                        dialog.show();
                    } else {
                        frappe.msgprint(__("Could not fetch customer info."));
                    }
                }
            });
        });

        // Handle Image Thumbnail click
        listview.page.container.on('click', '.image-thumbnail', function() {
            let image_link = $(this).data('image-link');
            let dialog = new frappe.ui.Dialog({
                title: __('Activity Photo'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'image_html',
                        options: `<img src="${image_link}" style="width: 100%; height: auto; object-fit: contain;">`
                    }
                ],
                size: 'small',
                primary_action_label: __('Close'),
                primary_action: function() {
                    dialog.hide();
                }
            });
            dialog.show();
        });
    },

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