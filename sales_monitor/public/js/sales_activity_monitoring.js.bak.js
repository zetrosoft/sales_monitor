// for sales_activity_monitoring.js
frappe.ui.form.on('Sales Activity Monitoring', {
    // Custom form logic can go here if needed
});

frappe.listview_settings['Sales Activity Monitoring'] = {
    refresh: function(listview) {
        console.log("ListView refresh triggered. Waiting for DOM...");

        // Add a small delay to ensure DOM is ready and data is populated
        setTimeout(() => {
            if (!listview && !listview.wrapper && !listview.data) {
                console.error("ListView data or wrapper not available after delay. Cannot process rows.");
                return;
            }
            console.log("ListView data and wrapper available. Processing rows...",listview);

            // Manually hide columns by targeting their headers
            listview.wrapper.find('.list-row-head [data-fieldname="name"]').hide();
            listview.wrapper.find('.list-row-head [data-fieldname="latitude"]').hide();
            listview.wrapper.find('.list-row-head [data-fieldname="longitude"]').hide();

            // Iterate over each row to manually format
            listview.data.forEach(doc => {
                console.log("Row data for formatter:", doc); // Keep this log as requested

                // Find the specific row element in the DOM
                let row = listview.wrapper.find(`.list-row[data-name="${doc.name}"]`);

                // Hide the data cells for the columns we don't want to see
                row.find('.list-row-col[data-fieldname="name"]').hide();
                row.find('.list-row-col[data-fieldname="latitude"]').hide();
                row.find('.list-row-col[data-fieldname="longitude"]').hide();

                // Manually create and inject the map icon
                if (doc.latitude && doc.longitude) {
                    let map_cell = row.find('.list-row-col[data-fieldname="map_link"]');
                    let map_html = `<span class="map-icon-trigger text-primary"
                                          data-lat="${doc.latitude}"
                                          data-lon="${doc.longitude}"
                                          data-customer="${doc.customer || 'Lokasi'}"
                                          style="cursor: pointer;">
                                       <i class="fa fa-map-marker fa-lg"></i>
                                   </span>`;
                    map_cell.find('div').html(map_html);
                }

                // Manually create and inject the image thumbnail
                if (doc.image_link) {
                    let image_cell = row.find('.list-row-col[data-fieldname="image_link"]');
                    let image_html = `<div class="image-thumbnail-wrapper" style="cursor: pointer;">
                                        <img src="${doc.image_link}" alt="Photo" style="height: 35px; width: 35px; object-fit: cover; border-radius: 5px;">
                                      </div>`;
                    image_cell.find('div').html(image_html);
                }
            });
        }, 500); // 500ms delay
    }
};