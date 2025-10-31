frappe.ui.form.on('Sales Visit Plan', {
    setup: function(frm) {
        // Set query for the 'sales_person' field
        frm.set_query("sales_person", function() {
            return {
                query: "sales_monitor.sales_monitor.doctype.sales_visit_plan.sales_visit_plan.get_sales_team_employees"
            };
        });
    },

    refresh: function(frm) {
        // Make sales_person read-only if the document is submitted
        if (frm.doc.docstatus === 1) {
            frm.set_df_property("sales_person", "read_only", 1);
        } else {
            frm.set_df_property("sales_person", "read_only", 0);
        }

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

        // Hide the default Submit button
        frm.remove_custom_button('Submit');

        // Add custom button for submit if status is Draft AND user has submit permission
        if (frm.doc.docstatus === 0 && frm.doc.status === 'Draft' && frm.perm[0].submit) {
            frm.add_custom_button(__("Submit Plan"), function() {
                frm.set_value('status', 'Planned');
                frm.save('Submit');
            }, 'Actions');
        }

        // Add custom button for cancel if status is Planned or Checked In
        if (frm.doc.docstatus === 1 && (frm.doc.status === 'Planned' || frm.doc.status === 'Checked In')) {
            frm.add_custom_button(__('Cancel Plan'), function() {
                frm.call({
                    method: 'sales_monitor.sales_monitor.doctype.sales_visit_plan.sales_visit_plan.cancel_sales_visit_plan',
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

        // Set default visit_time for new rows in child table
        if (frm.fields_dict['visit_plan_items'] && frm.fields_dict['visit_plan_items'].grid) {
            frm.fields_dict['visit_plan_items'].grid.wrapper.on('grid_rows_add', function(e, rows) {
                rows.forEach(function(row) {
                    if (row.__islocal && !row.doc.visit_time) {
                        frappe.model.set_value(row.doc.doctype, row.doc.name, 'visit_time', '07:00:00');
                    }
                });
            });
        }
    },

    before_submit: function(frm) {
        frm.set_value('status', 'Planned');
    },

    sales_person: function(frm) {
        if (frm.doc.sales_person) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Employee',
                    fieldname: ['user_id', 'employee_name'],
                    filters: {
                        name: frm.doc.sales_person
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('sales_id', r.message.user_id);
                        frm.set_value('employee_name', r.message.employee_name); // Set employee_name
                    }
                }
            });
        } else {
            frm.set_value('sales_id', '');
            frm.set_value('employee_name', ''); // Clear employee_name as well
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
                        let cleaned_address = r.message.primary_address.replace(/<br\s*\/?>/gi, ' '); // Replace <br> tags with space
                        frappe.model.set_value(cdt, cdn, 'address', cleaned_address);
                        console.log('Address set to:', cleaned_address);
                    } else {
                        console.log('No primary_address found or error in response.');
                    }
                }
            });
        }
    }
});