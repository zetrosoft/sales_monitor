app_name = "sales_monitor"
app_title = "Sales Monitor"
app_publisher = "Gemini"
app_description = "Sales monitoring and visit planning app"
app_email = "gemini@example.com"
app_license = "MIT"

app_include_css = "/assets/sales_monitor/css/sales_monitor.css"
app_include_js = "/assets/sales_monitor/js/sales_monitor.js"

desktop_icons = "sales_monitor.config.desktop.get_data"

fixtures = [
    {
        "doctype": "Workspace",
        "filters": {
            "name": "Sales Monitor"
        }
    },
    {
        "doctype": "DocType",
        "filters": {
            "name": ["in", ["Sales Activity Log", "Sales Visit Plan"]]
        }
    }
]