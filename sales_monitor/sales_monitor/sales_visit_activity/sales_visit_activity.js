// for sales_visit_activity.js
frappe.ui.form.on('Sales Visit Activity', {
    refresh: function(frm) {
        // Logika kustom untuk Form View bisa ditambahkan di sini
    }
});

// Kustomisasi untuk List View
frappe.listview_settings['Sales Visit Activity'] = {
    formatters: {
        photo: function(value, doc) {
            if (value) {
                return `<div class="image-thumbnail-wrapper" style="cursor: pointer;">
                            <img src="${value}" 
                                 alt="Photo" 
                                 style="height: 30px; width: 30px; object-fit: cover; border-radius: 4px;">
                        </div>`;
            }
            return '';
        },
        map_link: function(value, doc) {
            if (doc.latitude && doc.longitude) {
                // Tambahkan nama customer ke data-attribute tombol
                return `<button class="btn btn-xs btn-default map-popup-trigger" 
                                data-latitude="${doc.latitude}" 
                                data-longitude="${doc.longitude}"
                                data-customer-name="${doc.customer || ''}">
                            <i class="fa fa-map-marker"></i> View Map
                        </button>`;
            }
            return value ? `<a href="${value}" target="_blank">${value}</a>` : '';
        }
    },

    onload: function(listview) {
        // Logika Popup Gambar (tetap sama)
        listview.wrapper.on('mouseenter', '.image-thumbnail-wrapper', function(e) {
            let $target = $(e.currentTarget);
            let full_image_url = $target.find('img').attr('src');
            let popup = `<div class="image-popup" style="position: fixed; top: ${e.clientY + 15}px; left: ${e.clientX + 15}px; z-index: 100; background: white; border: 1px solid #ccc; padding: 5px; border-radius: 4px; box-shadow: 0 3px 6px rgba(0,0,0,0.1);">
                            <img src="${full_image_url}" style="max-width: 300px; max-height: 300px; border-radius: 4px;">
                         </div>`;
            $('body').append(popup);
        });
        listview.wrapper.on('mouseleave', '.image-thumbnail-wrapper', function() {
            $('.image-popup').remove();
        });

        // Logika untuk Popup Peta (dengan nama customer)
        listview.wrapper.on('click', '.map-popup-trigger', function(e) {
            e.preventDefault();
            e.stopPropagation();

            let $btn = $(e.currentTarget);
            let lat = $btn.data('latitude');
            let lon = $btn.data('longitude');
            let customerName = $btn.data('customer-name');
            
            // Encode nama customer untuk URL
            let encodedCustomerName = encodeURIComponent(customerName);

            // Tambahkan nama customer sebagai label di parameter q
            let map_html = `<iframe width="100%" height="400" frameborder="0" style="border:0"
                                src="https://maps.google.com/maps?q=${lat},${lon}+(${encodedCustomerName})&z=15&amp;output=embed" allowfullscreen>
                            </iframe>`;

            // Tambahkan nama customer ke judul dialog
            frappe.msgprint({
                title: __('Location Map for') + ' ' + customerName,
                message: map_html,
                wide: true
            });
        });
    }
};