frappe.listview_settings['Sales Activity Monitoring'] = {
    add_fields: ["name", "employee_name", "customer", "customer_address", "plan_date_time", "checkin_time", "checkout_time", "duration", "image_link", "map_link", "status", "latitude", "longitude"],
    get_list_method: "sales_monitor.api.get_sales_activity_monitoring_data",

    fields: [
        {fieldname: "name", label: __("ID")},
        {fieldname: "customer", label: __("Customer")},
        {fieldname: "plan_date_time", label: __("Plan Date")},
        {fieldname: "checkin_time", label: __("Visit Date")},
        {fieldname: "duration", label: __("Duration")},
        {fieldname: "image_link", label: __("Photo")},
        {fieldname: "map_link", label: __("Map")},
        {fieldname: "status", label: __("Status")}
    ],

    formatters: {
        customer: function(value, fieldname, doc) {
            console.log("Formatter called for customer:", fieldname, "Value:", value, "Doc data:", doc);
            if (doc.customer && doc.customer_address) {
                return `<span title="${doc.customer_address}">${value}</span>`;
            }
            return value;
        },
        plan_date_time: function(value, fieldname, doc) {
            if (doc.plan_date_time) {
                return frappe.datetime.str_to_user(doc.plan_date_time).split(" ")[0];
            }
            return "";
        },
        checkin_time: function(value, fieldname, doc) {
            if (doc.checkin_time) {
                return frappe.datetime.str_to_user(doc.checkin_time).split(" ")[0];
            }
            return "";
        },
        duration: function(value, fieldname, doc) {
            if (doc.duration) {
                let duration_text = doc.duration + " mins";
                let hover_text = "";
                if (doc.checkin_time && doc.checkout_time) {
                    hover_text = frappe.datetime.str_to_user(doc.checkin_time) + " - " + frappe.datetime.str_to_user(doc.checkout_time);
                }
                return `<span class="duration-popover" data-html="true" data-toggle="popover" data-placement="top" data-content="${hover_text}">${duration_text}</span>`;
            }
            return "";
        },
        map_link: function(value, fieldname, doc) {
            console.log("Formatter called for map_link:", fieldname, "Value:", value, "Doc data:", doc);
            if (doc.latitude && doc.longitude) {
                let url = `https://www.google.com/maps/search/?api=1&query=${doc.latitude},${doc.longitude}`;
                return `<a href="${url}" target="_blank" title="View on Map">
                <i class="fa fa-map-location" style="font-size: 1.5em;"></i>
            </a>`;
            }
            return "";
        },
        image_link: function(value, fieldname, doc) {
            console.log("Formatter called for image_link:", fieldname, "Value:", value, "Doc data:", doc);
            if (doc.image_link) {
                let escaped_image_link = frappe.utils.escape_html(doc.image_link);
                return `<a href="${escaped_image_link}" target="_blank">
                <img src="${escaped_image_link}" style="max-width: 50px; max-height: 50px; object-fit: cover; border-radius: 3px;"></a>`;
            }
            return "";
        }
    },

    onload: function(listview) {
        listview.page.wrapper.on("dblclick", ".list-row-container", function(e) {
            let docname = $(this).closest('.list-row-container').data('name');
            frappe.set_route("Form", "Sales Activity Monitoring", docname);
        });

        listview.page.container.on('mouseenter', '.customer-popover, .duration-popover', function() {
            $(this).popover('show');
        }).on('mouseleave', '.customer-popover, .duration-popover', function() {
            $(this).popover('hide');
        });

        listview.page.wrapper.on('click', '.map-icon', function(e) {
            e.stopPropagation();
            let lat = $(this).data('lat');
            let lon = $(this).data('lon');
            let customer = $(this).data('customer');
            let address = $(this).data('address');

            let dialog = new frappe.ui.Dialog({
                title: __('Visit Location'),
                fields: [
                    { fieldtype: 'HTML', fieldname: 'map' }
                ]
            });

            dialog.show();

            let map_element = dialog.get_field('map').$wrapper[0];
            map_element.style.height = "400px";

            let map = L.map(map_element).setView([lat, lon], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            L.marker([lat, lon]).addTo(map)
                .bindPopup(`<b>${customer}</b><br>${address}`)
                .openPopup();
        });

        listview.page.wrapper.on('click', '.image-thumbnail', function(e) {
            e.stopPropagation();
            let image_link = $(this).data('image-link');
            let dialog = new frappe.ui.Dialog({
                title: __('Activity Photo'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'image_html',
                        options: `<img src="${image_link}" style="width: 100%; height: auto; object-fit: contain;">`
                    }
                ]
            });
            dialog.show();
        });

        listview.page.add_inner_button(__("Show all on map"), function() {
            frappe.call({
                method: "sales_monitor.doctype.sales_activity_monitoring.sales_activity_monitoring.get_list",
                args: { 
                    limit_page_length: 0 // Get all records
                },
                callback: function(r) {
                    if (r.message) {
                        let dialog = new frappe.ui.Dialog({
                            title: __('All Visits Map'),
                            fields: [
                                { fieldtype: 'HTML', fieldname: 'map' }
                            ],
                            size: 'large'
                        });
                        dialog.show();

                        let map_element = dialog.get_field('map').$wrapper[0];
                        map_element.style.height = "600px";

                        let map = L.map(map_element).setView([-6.2088, 106.8456], 10); // Default view
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }).addTo(map);

                        r.message.forEach(function(activity) {
                            if (activity.latitude && activity.longitude) {
                                L.marker([activity.latitude, activity.longitude]).addTo(map)
                                    .bindPopup(`<b>${activity.customer}</b><br>${activity.customer_address}`);
                            }
                        });
                    }
                }
            });
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