frappe.ui.form.on('Sales Incentive Payment', {
    setup: function(frm) {
        frm.set_query('sales_person', function() {
            return {
                query: 'sales_monitor.sales_monitor.doctype.sales_incentive_payment.sales_incentive_payment.sales_person_query'
            };
        });
    },

    onload: function(frm) {
        // Set default Bulan
        if (frm.is_new() && !frm.doc.month) {
            const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
            frm.set_value('month', monthNames[new Date().getMonth()]);
        }
        
        // Set default Tahun (Fiscal Year)
        if (frm.is_new() && !frm.doc.year) {
            const currentYear = new Date().getFullYear().toString();
            // Frappe biasanya menggunakan tahun sebagai nama dokumen Fiscal Year
            frm.set_value('year', currentYear);
        }
    },

    sales_person: function(frm) { frm.trigger('process_incentive_data'); },
    month: function(frm) { frm.trigger('process_incentive_data'); },
    year: function(frm) { frm.trigger('process_incentive_data'); },

    on_submit: function(frm) {
        frappe.show_alert({
            message: __('Sales Incentive Payment berhasil disubmit.'),
            indicator: 'green'
        });
        frm.reload_doc();
    },

    process_incentive_data: function(frm) {
        if (!frm.doc.sales_person || !frm.doc.month || !frm.doc.year) {
            frm.clear_table('incentive_items');
            frm.set_value('grand_total', 0);
            return;
        }

        frm.call({
            method: 'sales_monitor.sales_monitor.doctype.sales_incentive_payment.sales_incentive_payment.process_sales_incentive',
            args: {
                sales_person_name: frm.doc.sales_person,
                month: frm.doc.month,
                year: frm.doc.year
            },
            freeze: true,
            callback: function(r) {
                if (r.message) {
                    frm.clear_table('incentive_items');
                    $.each(r.message.details, function(i, item) {
                        let d = frm.add_child('incentive_items');
                        d.tipe_incentive = item.tipe_incentive;
                        d.total_omset = item.total_omset;
                        d.jumlah = item.jumlah;
                        d.percentage = item.percentage;
                        d.bonus_omset = item.bonus_omset;
                        d.bonus_admin = item.bonus_admin;
                        d.total_bonus = item.total_bonus;
                    });
                    frm.set_value('applied_role', r.message.applied_role);
                    frm.set_value('active_scheme', r.message.active_scheme);
                    frm.set_value('grand_total', r.message.grand_total);
                    
                    frm.refresh_fields();
                    
                    frappe.show_alert({
                        message: __('Kalkulasi insentif granular selesai.'),
                        indicator: 'green'
                    });
                }
            }
        });
    }
});