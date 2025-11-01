const image_popover = $(`<div id="list-image-popover" style="display: none; position: fixed; z-index: 1001; background: #fff; border: 1px solid #ccc; padding: 5px; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"></div>`);
$('body').append(image_popover);

// Global functions to control the popover
window.show_image_popover = function(event, imageUrl) {
    image_popover.html(`<img src="${imageUrl}" style="max-width: 300px; max-height: 300px; object-fit: contain;">`);
    image_popover.css({
        top: (event.pageY + 10) + 'px',
        left: (event.pageX + 10) + 'px'
    }).show();
};

window.hide_image_popover = function() {
    image_popover.hide();
};

frappe.listview_settings['Sales Activity Monitoring'] = {
    fields: [
        "name",
        "customer",
        "sales_person",
        "plan_date_time",
        "checkin_time",
        "checkout_time",
        "duration",
        "status",
        "image_link"
    ],

    formatters: {
        image_link: function(value) {
            if (value) {
                // Inline event handlers that call the global functions
                return `<img src="${value}" 
                             style="width: 30px; height: 30px; object-fit: cover; border-radius: 4px;"
                             onmouseover="show_image_popover(event, '${value}')"
                             onmouseout="hide_image_popover()">`;
            }
            return "";
        }
    }
};