frappe.listview_settings['Sales Activity Monitoring'] = {
    onload: function(listview) {
        // No column filtering here.
    },

    formatters: {
        name: function(value) { // Formatter for the ID column
            // Ensure value is a string before calling toUpperCase()
            return (value && typeof value === 'string') ? value.toUpperCase() : (value || '');
        },
        image_link: function(value, field, doc) {
            if (value) {
                const thumbnail_url = frappe.utils.get_file_link(value);
                return `<div class="image-thumbnail-wrapper" data-image-url="${thumbnail_url}" style="cursor: pointer;">
                            <img src="${thumbnail_url}" alt="Photo" style="height: 35px; width: 35px; object-fit: cover; border-radius: 5px;">
                        </div>`;
            }
            return '';
        },
        map_link: function(value, field, doc) {
            if (doc.latitude && doc.longitude) {
                return `<span class="map-icon-trigger text-primary"
                              data-lat="${doc.latitude}"
                              data-lon="${doc.longitude}"
                              data-customer="${doc.customer || 'Lokasi'}"
                              style="cursor: pointer;">
                           <i class="fa fa-map-marker fa-lg"></i>
                        </span>`;
            }
            return '';
        }
    }
};

// Event handlers remain the same
$(document).on('mouseenter', '.list-row-container .image-thumbnail-wrapper', function(e) {
    if (!frappe.get_route() || frappe.get_route()[1] !== 'Sales Activity Monitoring') return;

    const imageUrl = $(this).data('image-url');
    if (imageUrl) {
        // Create and position the popup near the cursor
        let popup = `<div class="image-popup"
                     style="position: fixed;
                            top: ${e.clientY + 10}px;
                            left: ${e.clientX + 10}px;
                            z-index: 1001;
                            background: white;
                            border: 1px solid #d1d8dd;
                            padding: 8px;
                            border-radius: 6px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                    <img src="${imageUrl}" style="max-width: 300px; max-height: 300px; border-radius: 4px;">
                 </div>`;
        $('body').append(popup);
    }
});

$(document).on('mouseleave', '.list-row-container .image-thumbnail-wrapper', function(e) {
    if (!frappe.get_route() || frappe.get_route()[1] !== 'Sales Activity Monitoring') return;
    $('.image-popup').remove();
});

$(document).on('mousemove', '.list-row-container .image-thumbnail-wrapper', function(e) {
    if (!frappe.get_route() || frappe.get_route()[1] !== 'Sales Activity Monitoring') return;
    $('.image-popup').css({ top: e.clientY + 10, left: e.clientX + 10 });
});


// Event delegation for map popup (mouseenter)
$(document).on('mouseenter', '.list-row-container .map-icon-trigger', function(e) {
    if (!frappe.get_route() || frappe.get_route()[1] !== 'Sales Activity Monitoring') return;

    const lat = $(this).data('lat');
    const lon = $(this).data('lon');
    const customerName = $(this).data('customer');

    // Menggunakan OpenStreetMap embed URL
    const map_url = `https://www.openstreetmap.org/export/embed.html?bbox=${lon-0.01},${lat-0.01},${lon+0.01},${lat+0.01}&layer=mapnik&marker=${lat},${lon}`;

    // Create and position the popup near the cursor
    let popup = `<div class="map-popup"
                     style="position: fixed;
                            top: ${e.clientY + 10}px;
                            left: ${e.clientX + 10}px;
                            z-index: 1001;
                            background: white;
                            border: 1px solid #d1d8dd;
                            padding: 8px;
                            border-radius: 6px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                    <iframe width="300" height="200" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="${map_url}"></iframe>
                 </div>`;
    $('body').append(popup);
});

// Event delegation for map popup (mouseleave)
$(document).on('mouseleave', '.list-row-container .map-icon-trigger', function(e) {
    if (!frappe.get_route() || frappe.get_route()[1] !== 'Sales Activity Monitoring') return;
    $('.map-popup').remove();
});

// Event delegation for map popup (mousemove to follow cursor)
$(document).on('mousemove', '.list-row-container .map-icon-trigger', function(e) {
    if (!frappe.get_route() || frappe.get_route()[1] !== 'Sales Activity Monitoring') return;
    $('.map-popup').css({ top: e.clientY + 10, left: e.clientX + 10 });
});

//view form detail

frappe.ui.form.on('Sales Activity Monitoring', {
    refresh: function(frm) {
        // Sembunyikan field map_link dan image_link
        frm.set_df_property('map_link', 'hidden', 1);
        frm.set_df_property('image_link', 'hidden', 1);

        // Logika untuk menampilkan gambar
        if (frm.doc.image_link) {
            const image_url = frappe.utils.get_file_link(frm.doc.image_link);
            const image_html = `<img src="${image_url}" class="img-responsive" style="max-width: 400px; max-height: 400px;">`;
            frm.fields_dict.image_html.$wrapper.html(image_html);
        } else {
            frm.fields_dict.image_html.$wrapper.html("");
        }

        // Hapus elemen map yang sudah ada (jika ada) untuk menghindari duplikasi
        if (frm.fields_dict.map_html && frm.fields_dict.map_html.$wrapper) {
            frm.fields_dict.map_html.$wrapper.empty();
        }

        // Pastikan latitude dan longitude memiliki nilai
        if (frm.doc.latitude && frm.doc.longitude) {
            const lat = parseFloat(frm.doc.latitude);
            const lon = parseFloat(frm.doc.longitude);

            // URL OpenStreetMap Embed
            const map_url = `https://www.openstreetmap.org/export/embed.html?bbox=${(lon - 0.005)},${(lat - 0.005)},${(lon + 0.005)},${(lat + 0.005)}&layer=mapnik&marker=${lat},${lon}`;

            // Buat HTML untuk iframe peta
            const map_iframe = `
                <iframe width="100%" height="400" frameborder="0" style="border:0" 
                    src="${map_url}" allowfullscreen>
                </iframe>
            `;

            // CARA BENAR: Menggunakan properti $wrapper untuk mengubah konten HTML
            frm.fields_dict.map_html.$wrapper.html(map_iframe);
            
            // Mengubah label menggunakan metode yang benar
            frm.set_df_property('map_html', 'label', 'Lokasi di Peta (OpenStreetMap)');

        } else {
            // Sembunyikan field HTML jika data lat/long tidak tersedia
            frm.fields_dict.map_html.$wrapper.html("");
            frm.set_df_property('map_html', 'label', 'Lokasi di Peta (Tidak Tersedia)');
        }
    }
});