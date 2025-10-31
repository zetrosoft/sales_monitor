frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        render_map_in_tab(frm);

        setTimeout(function() {
            frm.get_field('address_on_map_tab').tab.wrapper.on('tab-shown', function() {
                if (frm.map) {
                    setTimeout(function() {
                        frm.map.invalidateSize();
                    }, 10);
                }
            });
        }, 100);
    }
});

function render_map_in_tab(frm) {
    const defaultLat = -6.4072702;
    const defaultLon = 106.6902876;

    let map_container = frm.get_field('map_html').$wrapper;
    map_container.empty().append('<div class="form-group"><input type="text" id="picked_address" class="form-control" readonly></div>');
    map_container.append('<div id="map_div" style="height: 400px; width: 100%;"></div>');

    let map = L.map('map_div').setView([frm.doc.custom_latitude || defaultLat, frm.doc.custom_longitude || defaultLon], 17);
    frm.map = map;
    //frm.map.invalidateSize();
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let marker = L.marker([frm.doc.custom_latitude || defaultLat, frm.doc.custom_longitude || defaultLon], { draggable: true }).addTo(map);

    const search = new GeoSearch.GeoSearchControl({
        provider: new GeoSearch.OpenStreetMapProvider({ 
            params: { 
                countrycodes: 'id'
            },
        }),
        style: 'bar',
        showMarker: false,
        autoClose: false,
    });
    map.addControl(search);

    map.on('geosearch/showlocation', function(result) {
        marker.setLatLng(result.location);
        reverseGeocodePopup(result.location.lat, result.location.lng, frm);
    });

    marker.on('dragend', function(e) {
        const latlng = marker.getLatLng();
        reverseGeocodePopup(latlng.lat, latlng.lng, frm);
    });

    // Add a button to save the address
    map_container.append('<div class="mt-3"><button class="btn btn-primary btn-sm" id="select_address_btn">Select Address</button></div>');

    $('#select_address_btn').on('click', function() {
        const latlng = marker.getLatLng();
        const pickedAddress = frm.picked_address_text;

        if (!pickedAddress) {
            frappe.msgprint(__('Please select an address on the map.'));
            return;
        }

        frm.set_value('custom_picked_address', pickedAddress);

        frappe.call({
            method: 'sales_monitor.api.create_address_from_map',
            args: {
                customer_name: frm.doc.name,
                address_title: pickedAddress,
                address_line1: pickedAddress,
                latitude: latlng.lat,
                longitude: latlng.lng
            },
            callback: function(r) {
                if (r.message) {
                    const newAddressName = r.message;
                    frm.set_value('customer_primary_address', newAddressName);
                    frm.set_value('custom_latitude', latlng.lat);
                    frm.set_value('custom_longitude', latlng.lng);
                    frappe.msgprint(__('Address created and linked successfully.'));
                } else {
                    frappe.msgprint(__('Failed to create address.'));
                }
            }
        });
    });
}

function reverseGeocodePopup(lat, lon, frm) {
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.display_name) {
                const address = data.display_name;
                frm.picked_address_text = address;
                $('#picked_address').val(address);
                // Update the search box with the address
                const searchBox = document.querySelector('.geosearch .glass input[type="text"]');
                if (searchBox) {
                    searchBox.value = address;
                }
            }
        })
        .catch(error => {
            console.error('Reverse geocoding error:', error);
            frappe.msgprint(__('Error during reverse geocoding.'));
        });
}
