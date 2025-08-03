import os
import json
from frappe import _

def get_data():
    with open(os.path.join(os.path.dirname(__file__), "..", "workspace", "sales_monitor_workspace.json"), "r") as f:
        workspace_data = json.load(f)
    return [
        {
            "module_name": "Sales Monitor",
            "color": "#757575",
            "icon": "octicon octicon-briefcase",
            "type": "module",
            "label": _("Sales Monitor"),
            "link": "sales-monitor",
            "is_workspace": True,
            "workspace_name": workspace_data.get("label", "Sales Monitor")
        }
    ]