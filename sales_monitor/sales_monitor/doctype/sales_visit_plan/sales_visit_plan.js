frappe.ui.form.on('Sales Visit Plan', {
    setup: function(frm) {
        // Any setup that doesn't depend on rendered fields can go here
    },

    refresh: function(frm) {
        // Set query for 'customer' field in 'visit_plan_items' child table
        // This needs to be in refresh to ensure the grid is rendered
        if (frm.fields_dict['visit_plan_items'] && frm.fields_dict['visit_plan_items'].grid) {
            frm.fields_dict['visit_plan_items'].grid.get_field('customer').set_query(function(doc, cdt, cdn) {
                return {
                    filters: {
                        'is_customer': 1
                    }
                };
            });
        }

        // Auto-populate sales_id and planned_visit_date on new documents
        if (frm.is_new()) {
            if (!frm.doc.sales_person) {
                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'Employee',
                        fieldname: 'name',
                        filters: {
                            user_id: frappe.session.user
                        }
                    },
                    callback: function(r) {
                        if (r.message) {
                            frm.set_value('sales_person', r.message.name);
                        }
                    }
                });
            }
            
            if (!frm.doc.planned_visit_date) {
                frm.set_value('planned_visit_date', frappe.datetime.get_today());
            }

            // Auto-populate number field
            // if (!frm.doc.number) {
            //     frappe.call({
            //         method: 'sales_monitor.api.get_next_sales_visit_plan_number',
            //         callback: function(r) {
            //             if (r.message) {
            //                 frm.set_value('number', r.message);
            //             }
            //         }
            //     });
            // }
        }

        // Add custom button for submit if status is Draft
        if (frm.doc.docstatus === 0 && frm.doc.status === 'Draft') {
            frm.add_custom_button(__('Submit Plan'), function() {
                frm.set_value('status', 'Planned');
                frm.save('Submit');
            }, 'Actions');
        }

        // Add custom button for cancel if status is Planned or Checked In
        if (frm.doc.docstatus === 1 && (frm.doc.status === 'Planned' || frm.doc.status === 'Checked In')) {
            frm.add_custom_button(__('Cancel Plan'), function() {
                frm.call({
                    method: 'sales_monitor.sales_monitor.doctype.sales_visit_plan.sales_visit_plan.on_cancel',
                    args: {
                        name: frm.doc.name
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }, 'Actions');
        }
    },

    sales_person: function(frm) {
        if (frm.doc.sales_person) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Employee',
                    fieldname: 'user_id',
                    filters: {
                        name: frm.doc.sales_person
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('sales_id', r.message.user_id);
                    }
                }
            });
        } else {
            frm.set_value('sales_id', '');
        }
    }
});

frappe.ui.form.on('Sales Visit Plan Item', {
    customer: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.customer) {
            console.log('Customer selected:', row.customer);
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Customer',
                    fieldname: 'primary_address',
                    filters: {
                        name: row.customer
                    }
                },
                callback: function(r) {
                    console.log('Frappe.call response:', r);
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'address', r.message.primary_address);
                        console.log('Address set to:', r.message.primary_address);
                    } else {
                        console.log('No primary_address found or error in response.');
                    }
                }
            });
        }
    }
});