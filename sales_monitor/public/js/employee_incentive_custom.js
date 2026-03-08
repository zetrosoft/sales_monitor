console.log("[Sales Monitor] employee_incentive_custom.js loaded");

frappe.ui.form.on('Employee Incentive', {
    refresh: function(frm) {
        console.log("[Sales Monitor] Employee Incentive refresh event triggered.");

        // Hapus tombol atau link lama jika ada
        frm.clear_custom_buttons();

        // Cari Payroll Entry yang sudah ada untuk Employee Incentive ini
        frappe.call({
            method: 'sales_monitor.override_payroll.get_existing_incentive_payroll_entry',
            args: {
                employee_incentive_name: frm.doc.name
            },
            callback: function(r) {
                console.log("[Sales Monitor] Callback from get_existing_incentive_payroll_entry. Response:", r.message);
                let existing_pe = r.message;
                if (frm.doc.docstatus === 1) { // Hanya muncul jika Employee Incentive sudah disubmit
                    if (!existing_pe) {
                        console.log("[Sales Monitor] No existing Payroll Entry found. Adding 'Create Incentive Payroll' button.");
                        frm.add_custom_button(__('Create Incentive Payroll'), function() {
                            frm.call({
                                method: 'sales_monitor.override_payroll.create_incentive_payroll_entry',
                                args: {
                                    employee_incentive_name: frm.doc.name
                                },
                                freeze: true,
                                btn_text: __('Creating Payroll Entry...'),
                                callback: function(r) {
                                    if (r.message) {
                                        frappe.msgprint(__('Payroll Entry {0} created successfully.', [r.message]));
                                        frm.reload_doc(); // Muat ulang dokumen untuk menampilkan link baru
                                    }
                                }
                            });
                        });
                        frm.change_custom_button_type(__('Create Incentive Payroll'), null, 'primary');
                    } else {
                        console.log("[Sales Monitor] Existing Payroll Entry found:", existing_pe, ". Adding 'View Payroll Entry' button.");
                        // Jika sudah ada PE yang dibuat, tampilkan link
                        frm.add_custom_button(__(existing_pe), function() {
                            frappe.set_route('Form', 'Payroll Entry', existing_pe);
                        }, __('View Payroll Entry'), 'btn-default');
                    }
                } else {
                    console.log("[Sales Monitor] Document status is not 1 (Submitted). No button will be added.");
                }
            }
        });
    }
});