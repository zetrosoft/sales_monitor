// Ensure frappe.pages object exists globally.
// This is a safe way to declare a namespace.
frappe.provide("frappe.pages");

// Explicitly check and initialize the specific page object if it doesn't exist.
// This prevents the TypeError: Cannot set properties of undefined.
if (!frappe.pages['sales-person-visit-metric-html']) {
    frappe.pages['sales-person-visit-metric-html'] = {};
}

// Assign the on_page_load function to the now guaranteed-to-exist page object.
// Frappe's page renderer will call this function when the page route is active.
frappe.pages['sales-person-visit-metric-html'].on_page_load = function(wrapper) {
    // Instantiate our custom page logic class.
    new SalesPersonVisitMetric(wrapper);
};

// Define the main class that encapsulates the page's logic and rendering.
// This class is instantiated when Frappe's on_page_load hook fires.
class SalesPersonVisitMetric {
    constructor(wrapper) {
        // Create the main app page structure provided by Frappe UI.
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: __("Sales Person Visit Metric (HTML)"), // Localized title
            single_column: true // Use a single column layout for simplicity
        });
        this.wrapper = wrapper; // Store the wrapper for future reference
        this.make_page(); // Initialize the page's content and logic
    }

    // Sets up the initial structure of the page, including filter elements.
    make_page() {
        // Render the basic HTML structure from the template into the page body.
        // The template now primarily provides containers for filters and the report table.
        $(this.page.body).html(frappe.render_template('sales_person_visit_metric_html'));
        // Identify the content area within the rendered template.
        this.page.content = $(this.page.body).find('.page-content');
        
        this.setup_filters(); // Configure date filters
        this.setup_primary_action(); // Configure the refresh button
        this.load_data(); // Load report data on initial page load
    }
    
    // Configures the date input fields with default values.
    setup_filters() {
        // Get today's date and calculate a date one month ago for default filter range.
        const today = frappe.datetime.now_date();
        const one_month_ago = frappe.datetime.add_months(today, -1);

        // Set the default values for the date input fields.
        $('#filter-from-date').val(one_month_ago);
        $('#filter-to-date').val(today);
    }

    // Sets up the primary action button (Refresh) in the page header.
    setup_primary_action() {
        this.page.set_primary_action(__('Refresh'), () => this.load_data(), 'refresh');
    }

    // Fetches report data from the server.
    load_data() {
        // Get filter values from the input fields.
        const from_date = $('#filter-from-date').val();
        const to_date = $('#filter-to-date').val();

        // Basic validation for date filters.
        if (!from_date || !to_date) {
            frappe.msgprint(__("Please select both 'From Date' and 'To Date'"));
            return;
        }

        const report_container = $('#report-container');
        // Display a loading spinner while data is being fetched.
        report_container.html(`<div class="text-center p-5 text-muted">
            <div class="spinner-border text-primary" role="status"></div>
            <br>${__('Loading data...')}
        </div>`);

        // Make an AJAX call to the Python backend to get report data.
        frappe.call({
            method: 'sales_monitor.sales_monitor.page.sales_person_visit_metric_html.sales_person_visit_metric_html.get_report_data',
            args: {
                date_from: from_date,
                date_to: to_date,
            },
            callback: (r) => {
                // Check if the call was successful and returned data without an error.
                if (r.message && !r.message.error) {
                    this.render_report(r.message); // Render the report table.
                } else {
                    // Display an error message if the backend call failed.
                    const error_msg = r.message ? r.message.error : __("Failed to fetch report data.");
                    report_container.html(`<div class="alert alert-danger">${error_msg}</div>`);
                }
            },
            error: () => {
                 // Display a generic error message for unexpected AJAX failures.
                 report_container.html(`<div class="alert alert-danger">${__("An unexpected error occurred.")}</div>`);
            }
        });
    }

    // Renders the report table based on the data received from the server.
    render_report(data) {
        const { header_rows, columns, data: report_data, filters } = data;
        
        // Construct the table header (<thead>) dynamically, handling two-row headers.
        const header_html = `
            <thead>
                <tr>
                    ${header_rows[0].map(col => `<th class="text-center align-middle" colspan="${col.colspan || 1}" rowspan="${col.rowspan || 1}">${__(col.label)}</th>`).join('')}
                </tr>
                <tr>
                    ${header_rows[1].map(col => col.hidden ? '' : `<th class="text-center align-middle">${__(col.label)}</th>`).join('')}
                </tr>
            </thead>
        `;
        
        // Construct the table body (<tbody>) dynamically.
        let body_html = '<tbody>';
        if (report_data.length === 0) {
            // Display a "No data found" message if the report_data is empty.
            const colspan = columns.length; // Calculate colspan based on total columns.
            body_html += `<tr><td colspan="${colspan}" class="text-center p-4 text-muted">${__("No data found for the selected period.")}</td></tr>`;
        } else {
            // Iterate through each row of data and construct table rows (<tr>) and cells (<td>).
            report_data.forEach((row, index) => {
                body_html += '<tr>';
                body_html += `<td class="text-center">${index + 1}</td>`; // Display row number.
                body_html += `<td style="font-weight: bold;">${row.sales_person_name || row.sales_person}</td>`; // Display sales person name.
                
                // Iterate through dynamic columns (starting from the third column, skipping No and Name).
                for (let j = 2; j < columns.length; j++) {
                    const col = columns[j];
                    const val = row[col.fieldname]; // Get the value for the current cell.
                    let cell_content = '';

                    // Apply specific formatting for boolean-like values (1/0 to checkmark/cross).
                    if (val === 1) {
                        cell_content = `<span class="text-success bold">✔</span>`;
                    } else if (val === 0) {
                        cell_content = `<span class="text-danger bold">✘</span>`;
                    } else {
                        // Use Frappe's formatter for other data types.
                        cell_content = frappe.format(val, col, {always_show_decimals: true});
                    }
                    body_html += `<td class="text-center">${cell_content}</td>`;
                }
                body_html += '</tr>';
            });
        }
        body_html += '</tbody>';

        // Assemble the complete HTML for the report table.
        const table_html = `
            <div class="report-wrapper" style="padding: 15px;">
                <div class="table-responsive">
                    <table class="table table-bordered table-sm table-hover" style="font-size: 12px;">
                        ${header_html}
                        ${body_html}
                    </table>
                </div>
            </div>
        `;
        
        // Inject the generated table HTML into the report container.
        $('#report-container').html(table_html);
    }
}