app_name = "sales_monitor"
app_title = "Sales Monitor"
app_publisher = "Bijak techno"
app_description = "Sales monitoring and visit planning app"
app_email = "support@bijaktechnology.com"
app_license = "MIT"

# App-level Includes
#app_include_css = "/assets/sales_monitor/css/sales_monitor.css"
app_include_js = ["/assets/sales_monitor/js/sales_activity_monitoring.js"]

# Doctype Specific Customizations
doctype_js = {
    "Sales Visit Plan": "sales_monitor/sales_monitor/doctype/sales_visit_plan/sales_visit_plan.js",
}

doctype_list_js = {
    "Sales Visit Plan": "sales_monitor/sales_monitor/doctype/sales_visit_plan/sales_visit_plan_list.js",

}

fixtures = ["Workspace"]

# Other Hooks
# desktop_icons = "sales_monitor.config.desktop.get_data"
