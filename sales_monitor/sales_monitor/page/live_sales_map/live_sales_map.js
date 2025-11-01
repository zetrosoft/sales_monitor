frappe.pages['live-sales-map'].on_page_load = function(wrapper) {
    console.log("Live Sales Map: Page load started.");
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Live Sales Activity Map',
        single_column: true
    });

    let container = $(wrapper).find('.layout-main-section');
    container.append(`
        <div class="live-sales-map-filters row" style="padding: 15px;">
            <div class="col-md-3">
                <div id="sales-person-filter-area"></div>
            </div>
            <div class="col-md-3">
                <div id="date-filter-area"></div>
            </div>
            <div class="col-md-2">
                <button class="btn btn-primary" id="refresh-map-btn">Show on Map</button>
            </div>
        </div>
        <div id="map-container" style="height: 600px; width: 100%;" class="mt-4"></div>
    `);

    // --- Create Filter Fields ---
    page.sales_person_filter = frappe.ui.form.make_control({
        parent: container.find('#sales-person-filter-area'),
        df: {
            fieldtype: 'Link',
            label: 'Sales Person',
            options: 'Employee',
            fieldname: 'sales_person',
            get_query: function() {
                return {
                    query: "sales_monitor.sales_monitor.page.live_sales_map.live_sales_map.get_sales_team_employees"
                }
            },
            read_only: frappe.user.has_role('Sales User') ? 1 : 0 // Set read_only directly in df
        },
        render_input: true,
    });
    console.log("Live Sales Map: Sales Person filter created.");

    page.date_filter = frappe.ui.form.make_control({
        parent: container.find('#date-filter-area'),
        df: {
            fieldtype: 'Date',
            label: 'Visit Date',
            fieldname: 'visit_date',
            default: frappe.datetime.get_today()
        },
        render_input: true,
    });
    console.log("Live Sales Map: Date filter created.");

    // --- Map variables ---
    let map;
    let markers = [];
    const icons = {
        Visited: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
        Planned: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
    };

    // --- Role-based Logic ---
    console.log("Live Sales Map: Checking user role.");
    if (frappe.user.has_role('Sales User')) {
        console.log("Live Sales Map: User is Sales User. Fetching employee name.");
        frappe.db.get_value('Employee', { 'user_id': frappe.session.user }, 'name', (r) => {
            console.log("Live Sales Map: Employee name fetched callback.", r);
            if (r && r.name) {
                page.sales_person_filter.set_value(r.name);

                console.log("Live Sales Map: Sales Person filter set and read-only. Triggering click.");
                container.find('#refresh-map-btn').trigger('click');
            }
        });
    } else {
        console.log("Live Sales Map: User is not Sales User.");
    }

    // --- Map and Button Logic ---
    function init_map() {
        console.log("Live Sales Map: init_map called.");
        if (!map) {
            map = new google.maps.Map(document.getElementById('map-container'), {
                center: { lat: -6.2088, lng: 106.8456 }, // Default to Jakarta
                zoom: 10
            });
            console.log("Live Sales Map: Map initialized.");
        }
    }

    function clear_markers() {
        console.log("Live Sales Map: clear_markers called.");
        for (let i = 0; i < markers.length; i++) {
            markers[i].setMap(null);
        }
        markers = [];
        console.log("Live Sales Map: Markers cleared.");
    }

    container.find('#refresh-map-btn').on('click', function() {
        console.log("Live Sales Map: 'Show on Map' button clicked.");
        const sales_person = page.sales_person_filter.get_value();
        const visit_date = page.date_filter.get_value();

        if (!sales_person || !visit_date) {
            frappe.msgprint(__('Please select Sales Person and Visit Date first.'));
            console.log("Live Sales Map: Validation failed - Sales Person or Visit Date missing.");
            return;
        }

        console.log("Live Sales Map: Calling backend get_todays_visits with", sales_person, visit_date);
        frappe.call({
            method: "sales_monitor.sales_monitor.page.live_sales_map.live_sales_map.get_todays_visits",
            args: {
                sales_person: sales_person,
                visit_date: visit_date
            },
            callback: function(r) {
                console.log("Live Sales Map: Backend callback received.", r);
                init_map();
                clear_markers();
                if (r.message && r.message.length > 0) {
                    console.log("Live Sales Map: Rendering pins.", r.message.length, "pins.");
                    let bounds = new google.maps.LatLngBounds();
                    r.message.forEach(point => {
                        const position = { lat: point.lat, lng: point.lng };
                        const marker = new google.maps.Marker({
                            position: position,
                            map: map,
                            title: point.customer,
                            icon: icons[point.status]
                        });

                        if (point.status === 'Visited' && point.photo) {
                            const info_content = `<div><strong>${point.customer}</strong><br><img src="${point.photo}" style="width:150px;height:auto;"></div>`;
                            const infowindow = new google.maps.InfoWindow({ content: info_content });
                            marker.addListener('mouseover', () => infowindow.open(map, marker));
                            marker.addListener('mouseout', () => infowindow.close());
                        }
                        markers.push(marker);
                        bounds.extend(position);
                    });
                    map.fitBounds(bounds);
                    console.log("Live Sales Map: Pins rendered and map fitted.");
                } else {
                    frappe.show_alert({ message: __('No visits found for the selected criteria.'), indicator: 'info' });
                    console.log("Live Sales Map: No visits found.");
                }
            }
        });
    });
    console.log("Live Sales Map: Page load finished.");
}
