
// Copyright (c) 2025, [Your Name] and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Visit Activity', {
    refresh: function(frm) {
        // Disable the "Add New" button
        frm.page.clear_primary_action();
    }
});

frappe.listview_settings['Sales Visit Activity'] = {
    // Custom formatters for data display
    formatters: {
        sales_person(val, doc) {
            // This is the first column, by returning a simple string, we remove the link to the form view.
            return doc.sales_person;
        },
        customer(val, doc) {
            if (val) {
                // Fetch customer address and show in popover
                frappe.db.get_value('Customer', val, 'customer_primary_address', (r) => {
                    if (r && r.customer_primary_address) {
                        $(`[data-name="${doc.name}"] .list-subject .customer-popover`).attr('title', r.customer_primary_address);
                    }
                });
                return `<span class="customer-popover" title="Loading address...">${val}</span>`;
            }
            return '';
        },
        plan_date_time(val) {
            if (val) {
                return moment(val).format('DD-MM-YYYY');
            }
            return '';
        },
        checkin_time(val) {
            if (val) {
                return moment(val).format('DD-MM-YYYY');
            }
            return '';
        },
        duration(val) {
            if (val > 0) {
                let hours = Math.floor(val / 3600);
                let minutes = Math.floor((val % 3600) / 60);
                if (hours > 0) {
                    return `${hours} Jam ${minutes} Menit`;
                } else {
                    return `${minutes} Menit`;
                }
            }
            return '0 Menit';
        },
        image_link(val) {
            if (val) {
                return `<a href="${val}" target="_blank" title="View Image"><i class="fa fa-camera"></i></a>`;
            }
            return '';
        },
        map_link(val, doc) {
            let lat = doc.latitude;
            let lon = doc.longitude;
            let link = val;
            if (!link && lat && lon) {
                link = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
            }

            if (link) {
                return `<a href="${link}" target="_blank" title="View on Map"><i class="fa fa-map-marker"></i></a>`;
            }
            return '';
        }
    },

    // Disable single click action
    get_indicator: function(doc) {
        return [__("Not set"), "grey", ""]; // No status indicator
    },
    
    onload: function(listview) {
        // Disable the "Add New" button
        listview.page.clear_primary_action();

        // Add custom filters
        listview.page.add_field({
            fieldname: 'sales_person_filter',
            label: __('Sales Person'),
            fieldtype: 'Link',
            options: 'Sales Person',
            change: () => listview.refresh(),
        });

        listview.page.add_field({
            fieldname: 'customer_filter',
            label: __('Customer'),
            fieldtype: 'Link',
            options: 'Customer',
            change: () => listview.refresh(),
        });

        listview.page.add_field({
            fieldname: 'date_range_filter',
            label: __('Date Range'),
            fieldtype: 'DateRange',
            change: () => listview.refresh(),
        });
    }
};
