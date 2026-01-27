frappe.provide("frappe.pages");

frappe.pages['sales_person_visit_metric_html'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Sales Person Visit Metric"),
        single_column: true
    });

    // 1. Render Struktur Utama UI
    $(page.body).html(`
        <div class="frappe-card">
            <div class="p-3 border-bottom bg-light">
                <div class="row">
                    <div class="col-md-3">
                        <label class="small text-muted">Dari Tanggal</label>
                        <input type="date" id="f-from" class="form-control input-sm auto-reload">
                    </div>
                    <div class="col-md-3">
                        <label class="small text-muted">Sampai Tanggal</label>
                        <input type="date" id="f-to" class="form-control input-sm auto-reload">
                    </div>
                    <div class="col-md-3">
                        <label class="small text-muted">Sales Person</label>
                        <select id="f-sales" class="form-control input-sm auto-reload">
                            <option value="">-- Semua Sales --</option>
                        </select>
                    </div>
                </div>
            </div>
            <div id="report-output-container" class="p-3"></div>
        </div>
        <style>
            /* Gaya Tabel Report */
            .table-report thead th { 
                border: 1px solid #d1d8dd !important; 
                text-align: center; 
                vertical-align: middle !important; 
                background: #f8f9fa; 
                font-weight: bold; 
            }
            .table-report tbody td { 
                border: 1px solid #d1d8dd !important; 
                text-align: center; 
                vertical-align: middle; 
                color: #000;
            }
            /* Kolom Sticky untuk Nama Sales */
            .sticky-col { 
                position: sticky; 
                left: 0; 
                background: white !important; 
                z-index: 10; 
                border-right: 2px solid #d1d8dd !important; 
                min-width: 180px; 
                text-align: left !important; 
                font-weight: bold; 
            }
            /* Highlight jika ada angka > 0 */
            .positive-value { 
                background-color: #fffde7 !important; 
                border: 2px solid #2196f3 !important;
                color: #0d47a1 !important; 
                font-weight: bold;
            }
            .table-responsive {
                max-height: 75vh;
                overflow: auto;
            }
        </style>
    `);

    // 2. Load Data Dropdown Sales Person dari Server
    const load_dropdown = () => {
        frappe.call({
            method: 'sales_monitor.sales_monitor.page.sales_person_visit_metric_html.sales_person_visit_metric_html.get_sales_persons',
            callback: (r) => {
                if (r.message) {
                    let $select = $('#f-sales');
                    $select.empty().append('<option value="">-- Semua Sales --</option>');
                    r.message.forEach(s => {
                        // Menggunakan s.name (ID) sebagai value, s.sales_person_name sebagai tampilan
                        $select.append(`<option value="${s.name}">${s.sales_person_name || s.name}</option>`);
                    });
                }
            }
        });
    };

    // 3. Set Default Filter (Tanggal)
    let today_date = frappe.datetime.now_date();
    $('#f-from').val(frappe.datetime.add_months(today_date, -1));
    $('#f-to').val(today_date);

    // 4. Fungsi Utama Memuat Data Report
    const load_report = () => {
        const $container = $('#report-output-container');
        $container.html('<div class="text-center p-5 text-muted"><div class="spinner-border spinner-border-sm"></div> Memuat data...</div>');

        frappe.call({
            method: 'sales_monitor.sales_monitor.page.sales_person_visit_metric_html.sales_person_visit_metric_html.get_report_data',
            args: {
                date_from: $('#f-from').val(),
                date_to: $('#f-to').val(),
                sales_person: $('#f-sales').val()
            },
            callback: (r) => {
                // DEBUG: Cek di console (F12) untuk melihat data yang dikirim server
                console.log("Data diterima:", r.message);

                if (r.message && r.message.error) {
                    $container.html(`<div class="alert alert-danger">${r.message.error}</div>`);
                } else if (r.message && r.message.data && r.message.data.length > 0) {
                    render_table(r.message);
                } else {
                    let debug_info = r.message?.debug_info ? `<br><small class="text-muted">ID Sent: ${r.message.debug_info.sales_person}</small>` : "";
                    $container.html(`
                        <div class="alert alert-warning text-center">
                            Data tidak ditemukan untuk filter ini. ${debug_info}
                        </div>
                    `);
                }
            }
        });
    };

    // 5. Fungsi Render Tabel HTML
    const render_table = (res) => {
        const { header_rows, columns, data } = res;
        const $container = $('#report-output-container');

        // Render Header
        let header_html = `
            <thead>
                <tr>${header_rows[0].map(h => `<th colspan="${h.colspan || 1}" rowspan="${h.rowspan || 1}">${h.label}</th>`).join('')}</tr>
                <tr>${header_rows[1].filter(h => !h.hidden).map(h => `<th style="font-size: 10px; padding: 4px;">${h.label}</th>`).join('')}</tr>
            </thead>
        `;

        // Render Body
        let body_html = '<tbody>';
        data.forEach((row, i) => {
            body_html += `<tr>
                <td>${i+1}</td>
                <td class="sticky-col">${row.sales_person_name || row.sales_person || '-'}</td>
                ${columns.slice(2).map(c => {
                    let val_str = row[c.fieldname] || "";
                    let sch = 0, visit = 0, order = 0;
                    
                    // Parsing data format "Sch:0 | Visit:0 | Order:0"
                    if (typeof val_str === 'string' && val_str.includes('|')) {
                        let parts = val_str.split('|');
                        sch = parseInt(parts[0].split(':')[1]) || 0;
                        visit = parseInt(parts[1].split(':')[1]) || 0;
                        order = parseInt(parts[2].split(':')[1]) || 0;
                    }

                    const f_cell = (val) => {
                        let cls = val > 0 ? 'positive-value' : '';
                        return `<td class="${cls}">${val}</td>`;
                    };

                    return f_cell(sch) + f_cell(visit) + f_cell(order);
                }).join('')}
            </tr>`;
        });
        body_html += '</tbody>';

        // Tampilkan Tabel ke Container
        $container.html(`
            <div class="table-responsive">
                <table class="table table-bordered table-sm table-report" style="font-size: 11px; min-width: 1500px; border-collapse: separate; border-spacing: 0;">
                    ${header_html}
                    ${body_html}
                </table>
            </div>
        `);
    };

    // 6. Event Listeners
    $('.auto-reload').on('change', () => load_report());

    // 7. Initial Execution
    load_dropdown();
    load_report();
};