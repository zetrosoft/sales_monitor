frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        // Hapus custom button lama (jika masih ada)
        frm.remove_custom_button(__('Pilih Alamat di Peta'), __('Alamat'));
        
        // Inisialisasi peta secara permanen di tab 'Address on map'
        initialize_permanent_map(frm);
    },

    after_save: function(frm) {
        // Cek jika ada flag bahwa alamat baru perlu dibuat
        if (frm.new_address_to_be_created) {
            // Reset flag segera untuk mencegah eksekusi ganda
            frm.new_address_to_be_created = false; 
            save_address_to_frappe(frm);
        }
    }
});

function initialize_permanent_map(frm) {
    // ID div peta yang akan dibuat
    const map_container_id = 'customer_permanent_map_canvas';
    
    // Fieldname HTML yang sudah didefinisikan di Custom Field Anda
    const map_field = frm.fields_dict.map_html; 
    
    if (!map_field) {
        console.warn("Field 'map_html' (Wadah Peta) tidak ditemukan di DocType Customer. Peta tidak dapat diinisialisasi.");
        return; 
    }

    // 1. Tentukan Koordinat Awal (Default Depok/Bogor)
    const default_lat = -6.4072702;
    const default_lng = 106.6902876;
    
    // Gunakan field custom_latitude/longitude yang tersimpan sebagai posisi awal
    const initial_lat = frm.doc.custom_latitude || default_lat;
    const initial_lng = frm.doc.custom_longitude || default_lng;

    const is_location_data_present = !!frm.doc.custom_picked_address;
    
    console.log("--- Debug Lokasi Tersimpan ---");
    console.log("custom_latitude:", frm.doc.custom_latitude);
    console.log("custom_longitude:", frm.doc.custom_longitude);
    console.log("custom_picked_address:", frm.doc.custom_picked_address);
    console.log("Status is_location_data_present:", is_location_data_present);
    console.log("------------------------------");
    
    const saved_address = frm.doc.custom_picked_address || '';
    
    const saved_info = is_location_data_present ? 
        `<strong>${__('Lokasi Tersimpan')}</strong>: Lat: ${parseFloat(initial_lat).toFixed(6)}, Lng: ${parseFloat(initial_lng).toFixed(6)}` + 
        (saved_address ? `<br>${saved_address}` : '')
        : `<strong>${__('Customer belum memiliki lokasi tersimpan.')}</strong> ${__('Gunakan peta di bawah untuk memilih.')}`;

    // Tombol akan selalu aktif di awal, logika disable dipindah ke on-click
    const save_button_disabled_state = '';

    // 2. Set up HTML Container dan Tombol Aksi
    map_field.$wrapper.empty().append(`
        <div id="saved-address-display" class="alert ${is_location_data_present ? 'alert-success' : 'alert-warning'} p-2 mb-3">
            ${saved_info}
        </div>

        <div class="form-group">
            <input type="text" id="map-search-input" class="form-control" placeholder="${__('Cari lokasi atau alamat...')}">
        </div>

        <div id="${map_container_id}" style="height: 400px; width: 100%; border-radius: 8px; margin-bottom: 15px;"></div>
        
        <div class="flex justify-between items-center mt-3">
            <span class="text-sm text-muted" id="selected-address-info" style="display: none;">${__('Memuat alamat dari Nominatim...')}</span>
            <button class="btn btn-primary btn-sm" id="btn-use-new-address" ${save_button_disabled_state}>
                ${__('Gunakan Alamat Ini')}
            </button>
        </div>
        <hr>
        <div class="small text-muted">${__('Pindahkan pin di peta atau klik lokasi baru. Klik "Gunakan Alamat Ini" lalu simpan Customer untuk membuat Dokumen Address baru.')}</div>
    `);

    // 3. Inisialisasi Google Maps
    try {
        if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
            map_field.$wrapper.find('#' + map_container_id).html(`<div class="alert alert-danger">${__('Google Maps API belum dimuat!')}</div>`);
            return;
        }

        let map = new google.maps.Map(document.getElementById(map_container_id), {
            center: { lat: parseFloat(initial_lat), lng: parseFloat(initial_lng) },
            zoom: 17,
            fullscreenControl: false,
            streetViewControl: false
        });

        let marker = new google.maps.Marker({
            position: { lat: parseFloat(initial_lat), lng: parseFloat(initial_lng) },
            map: map,
            draggable: true,
            title: __('Pindahkan Pin Ini')
        });

        const search_input = document.getElementById('map-search-input');
        const autocomplete = new google.maps.places.Autocomplete(search_input);
        autocomplete.bindTo('bounds', map);

        autocomplete.addListener('place_changed', function() {
            const place = autocomplete.getPlace();
            if (!place.geometry) {
                window.alert("No details available for input: '" + place.name + "'");
                return;
            }
            map.setCenter(place.geometry.location);
            map.setZoom(17);
            marker.setPosition(place.geometry.location);
            handle_map_interaction(place.geometry.location.lat(), place.geometry.location.lng());
        });
        
        frm.map_data = { 
            marker: marker, 
            selected_lat: initial_lat, 
            selected_lng: initial_lng,
            use_button: map_field.$wrapper.find('#btn-use-new-address')
        };

        const handle_map_interaction = (lat, lng) => {
            frm.map_data.selected_lat = lat;
            frm.map_data.selected_lng = lng;
            
            frm.fields_dict.map_html.$wrapper.find('#selected-address-info').show();
            frm.fields_dict.map_html.$wrapper.find('#saved-address-display').hide();

            // Aktifkan kembali tombol jika user berinteraksi lagi
            frm.map_data.use_button.prop('disabled', false);

            update_map_info(frm, lat, lng);
            
            frm.set_value('custom_latitude', lat);
            frm.set_value('custom_longitude', lng);
        };
        
        google.maps.event.addListener(marker, 'dragend', function() {
            const lat = marker.getPosition().lat();
            const lng = marker.getPosition().lng();
            handle_map_interaction(lat, lng);
        });

        google.maps.event.addListener(map, 'click', function(event) {
            marker.setPosition(event.latLng);
            const lat = event.latLng.lat();
            const lng = event.latLng.lng();
            handle_map_interaction(lat, lng);
        });

        // Event listener untuk tombol "Gunakan Alamat Ini"
        frm.map_data.use_button.on('click', () => {
            // Set flag untuk after_save
            frm.new_address_to_be_created = true;
            
            // Beri feedback ke user
            frappe.show_alert({
                message: __('Alamat baru akan dibuat saat Anda menyimpan Customer ini.'),
                indicator: 'info'
            }, 7);
            
            // Non-aktifkan tombol untuk mencegah klik ganda
            frm.map_data.use_button.prop('disabled', true);
        });

    } catch (e) {
        console.error("Map Initialization Error:", e);
        map_field.$wrapper.find('#' + map_container_id).html(`<div class="alert alert-danger">${__('Gagal memuat peta.')}</div>`);
    }
}

function update_map_info(frm, lat, lng) {
    const nominatim_url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`;
    const info_span = frm.fields_dict.map_html.$wrapper.find('#selected-address-info');

    info_span.html(`<i class="fa fa-spinner fa-spin"></i> ${__('Memuat alamat...')} (${lat.toFixed(6)}, ${lng.toFixed(6)})`);
    frm.map_data.nominatim_data = null; 

    fetch(nominatim_url)
        .then(response => {
            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            const address = data.address || {};
            const full_address_str = data.display_name || '';

            let street_address = full_address_str;
            const city_name = address.city || address.town || address.village || address.suburb;
            const state_name = address.state;

            if (city_name && street_address.includes(city_name)) {
                 street_address = street_address.substring(0, street_address.indexOf(city_name)).trim();
                 if (street_address.endsWith(',')) {
                     street_address = street_address.substring(0, street_address.length - 1).trim();
                 }
            } else if (state_name && street_address.includes(state_name)) {
                 street_address = street_address.substring(0, street_address.indexOf(state_name)).trim();
                 if (street_address.endsWith(',')) {
                     street_address = street_address.substring(0, street_address.length - 1).trim();
                 }
            }
            
            frm.map_data.nominatim_data = {
                address_title: full_address_str,
                raw_street_address: street_address,
                city: address.city || address.town || address.village || address.suburb || '',
                state: address.state || '',
                country: address.country || '',
                pincode: address.postcode || ''
            };
            
            frm.set_value('custom_picked_address', full_address_str);

            const pincode_display = frm.map_data.nominatim_data.pincode ? ` (${frm.map_data.nominatim_data.pincode})` : '';
            info_span.html(`
                **${__('Pilihan Baru')}**: ${lat.toFixed(6)}, ${lng.toFixed(6)} | 
                ${full_address_str.substring(0, 100)}... ${pincode_display}
            `);
        })
        .catch(error => {
            console.error('Nominatim Error:', error);
            info_span.text(`${__('Gagal mendapatkan alamat terstruktur.')} Koordinat: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
            frm.set_value('custom_picked_address', `Koordinat: ${lat.toFixed(6)}, ${lng.toFixed(6)}`); 
            
            frm.map_data.nominatim_data = {
                raw_street_address: `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`,
                city: '', state: '', country: 'Indonesia', pincode: ''
            };
        });
}

function save_address_to_frappe(frm) {
    if (frm.doc.__islocal) {
        frappe.msgprint(__('Customer harus disimpan terlebih dahulu sebelum dapat membuat Dokumen Address.'));
        return;
    }

    if (!frm.map_data || !frm.map_data.nominatim_data) {
        // Tidak perlu throw error, cukup batalkan jika tidak ada data
        console.log("save_address_to_frappe dibatalkan: tidak ada data nominatim.");
        return;
    }

    const data = frm.map_data.nominatim_data;
    const coords = { 
        latitude: frm.map_data.selected_lat, 
        longitude: frm.map_data.selected_lng 
    };
    
    const raw_address_chunks = data.raw_street_address.split(',').map(s => s.trim()).filter(s => s.length > 0);
    
    let final_address_line1 = "";
    let final_address_line2 = "";
    const chunk_count = raw_address_chunks.length;

    if (chunk_count > 3) {
        final_address_line1 = raw_address_chunks.slice(0, 3).join(', ');
        final_address_line2 = raw_address_chunks.slice(3).join(', ');
    } else {
        final_address_line1 = raw_address_chunks.join(', ');
        final_address_line2 = "";
    }
    
    const final_address_title = frm.doc.name;

    frappe.call({
        method: 'sales_monitor.apix.create_address_from_map',
        args: {
            customer_name: frm.doc.name,
            address_title: final_address_title, 
            address_line1: final_address_line1,
            address_line2: final_address_line2,
            latitude: coords.latitude,
            longitude: coords.longitude,
            city: data.city,
            state: data.state,
            country: data.country,
            pincode: data.pincode || "" 
        },
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Alamat baru dari peta berhasil dibuat!'),
                    indicator: 'green'
                }, 5); 
                
                // Reload form untuk menampilkan data terbaru di daftar alamat
                frm.reload_doc();
                
            } else if (r.exc) {
                 frappe.msgprint({
                    title: __('Gagal'),
                    message: __('Gagal membuat alamat. Silakan cek error log.'),
                    indicator: 'red'
                });
            }
        }
    });
}
