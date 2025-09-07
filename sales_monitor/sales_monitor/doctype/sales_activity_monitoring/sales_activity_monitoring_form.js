frappe.ui.form.on('Sales Activity Monitoring', {
    refresh: function(frm) {
        // Map Link (Geolocation Field)
        // Frappe should handle rendering Geolocation field automatically.
        // We just need to ensure latitude and longitude are correctly set in the doc.
        // Let's ensure the latitude and longitude fields are visible for debugging if needed.
        //frm.toggle_display(['latitude', 'longitude'], true); // Show for debugging
       // console.log("Latitude:", frm.doc.latitude, "Longitude:", frm.doc.longitude);
        // Image Link (Attach Image Field)
        // Frappe should handle rendering Attach Image field automatically.
        // We just need to ensure the image_link field has a valid file URL.
    }
});