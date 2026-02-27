import sales_monitor.config

app_name = "sales_monitor"
app_title = "Sales Monitor"
app_publisher = "Bijak techno"
app_description = "Sales monitoring and visit planning app"
app_email = "support@bijaktechnology.com"
app_license = "MIT"

# App-level Includes
#app_include_css = "/assets/sales_monitor/css/sales_monitor.css"
app_include_js = [
    f"https://maps.googleapis.com/maps/api/js?key={sales_monitor.config.google_maps_api_key}&libraries=places"
]

# Doctype Specific Customizations
doctype_js = {
    "Customer": "public/js/customer_map_picker_custom.js",
    "Sales Activity Monitoring": "sales_monitor/sales_monitor/doctype/sales_activity_monitoring/sales_activity_monitoring.js",
    "Sales Visit Plan": "sales_monitor/sales_monitor/doctype/sales_visit_plan/sales_visit_plan.js",
    "Employee Incentive": "public/js/employee_incentive_custom.js"
}

doctype_list_js = {
    "Sales Visit Plan": "sales_monitor/sales_monitor/doctype/sales_visit_plan/sales_visit_plan_list.js",
    "Sales Activity Monitoring": "public/js/sales_activity_monitoring_list.js"
}

page_js = {
    "sales-person-visit-metric-html": "sales_monitor/sales_monitor/page/sales_person_visit_metric_html/sales_person_visit_metric_html.js"
}

#fixtures = ["Workspace"]

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": {
            "dt_name": "Employee Incentive"
        }
    },
    {
        "doctype": "Custom Field",
        "filters": {
            "dt_name": "Payroll Entry"
        }
    }
]

# Other Hooks
# desktop_icons = "sales_monitor.config.desktop.get_data"

method_override = {
    "erpnext.payroll.doctype.salary_slip.salary_slip.calculate_net_pay": "sales_monitor.override_payroll.calculate_net_pay_override"
}