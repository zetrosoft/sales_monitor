frappe.ui.form.on('Sales Activity Monitoring', {
    refresh: function(frm) {
        const map_container_id = 'sales_activity_map_canvas';
        const default_hq_coords = { lat: -6.4044, lng: 106.6768 }; 

        let final_latitude = frm.doc.latitude;
        let final_longitude = frm.doc.longitude;
        
        if (frm.doc.customer) {
            frm.trigger("customer");
        } else {
            if (frm.fields_dict.customer_address_html) {
                frm.fields_dict.customer_address_html.$wrapper.html('');
            }
        }

        const render_map = (lat, lng) => {
            if (!frm.fields_dict.map_html) return;

            const map_wrapper = frm.fields_dict.map_html.$wrapper;
            map_wrapper.empty().append(`<div id="${map_container_id}" style="height: 400px; width: 100%; border-radius: 8px; cursor: pointer;"></div>`);

            // Use setTimeout to ensure the DOM is ready for Google Maps
            setTimeout(() => {
                if (typeof google === 'undefined' || typeof google.maps === 'undefined') return;
                let map = new google.maps.Map(document.getElementById(map_container_id), { center: { lat: parseFloat(lat), lng: parseFloat(lng) }, zoom: 17 });
                new google.maps.Marker({ position: { lat: parseFloat(lat), lng: parseFloat(lng) }, map: map, title: frm.doc.customer || 'PT. SIUMANG TEMAN SUKSES' });

                // Add click listener to the map container
                document.getElementById(map_container_id).addEventListener('click', () => {
                    frappe.confirm(
                        __('Lihat di Google Map?'),
                        () => {
                            const url = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
                            window.open(url, '_blank');
                        }
                    );
                });
            }, 100); // 100ms delay
        };

        const handle_no_location = () => {
            if (frm.fields_dict.map_html) {
                frm.fields_dict.map_html.$wrapper.empty().append(`<div class="alert alert-info">${__('Lokasi customer tidak ditemukan. Menggunakan lokasi default PT. Siumang Teman Sukses.')}</div>`);
            }
            render_map(default_hq_coords.lat, default_hq_coords.lng);
        };

        if (final_latitude && final_longitude) {
            render_map(final_latitude, final_longitude);
        } else if (frm.doc.customer) {
            frappe.db.get_value('Customer', frm.doc.customer, ['custom_latitude', 'custom_longitude'], (r) => {
                if (r && r.custom_latitude && r.custom_longitude) {
                    render_map(r.custom_latitude, r.custom_longitude);
                } else {
                    handle_no_location();
                }
            });
        } else {
            handle_no_location();
        }
        
        // --- Display Photo ---
        if (frm.doc.image_link) {
            if (frm.fields_dict.image_html) {
                frm.fields_dict.image_html.$wrapper.empty().append(`<img src="${frm.doc.image_link}" style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 15px;">`);
            }
        } else {
            if (frm.fields_dict.image_html) {
                frm.fields_dict.image_html.$wrapper.empty().append(`<img src="https://via.placeholder.com/150?text=No+Photo" style="max-width: 100%; height: auto; min-width: 100px; min-height: 100px; border-radius: 8px; margin-top: 15px; background-color: #f0f0f0; display: block;" alt="No Photo Available">`);
            }
        }
    },

    customer: function(frm) {
        const customer_address_field = 'customer_address_html';
        if (!frm.fields_dict[customer_address_field]) return;

        if (frm.doc.customer) {
            frappe.call({
                method: 'sales_monitor.sales_monitor.doctype.sales_activity_monitoring.sales_activity_monitoring.get_customer_address',
                args: { customer_name: frm.doc.customer },
                callback: function(r) {
                    if (r.message) {
                        frm.fields_dict[customer_address_field].$wrapper.html(r.message);
                        // Force the field to be visible
                        frm.set_df_property(customer_address_field, 'hidden', 0);
                        frm.refresh_field(customer_address_field);
                    } else {
                        frm.fields_dict[customer_address_field].$wrapper.html('');
                    }
                }
            });
        } else {
            frm.fields_dict[customer_address_field].$wrapper.html('');
        }
    }
});