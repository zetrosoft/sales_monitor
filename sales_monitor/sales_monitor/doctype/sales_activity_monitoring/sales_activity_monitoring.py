import frappe
from frappe.model.document import Document

class SalesActivityMonitoring(Document):
    # Frappe will automatically handle get_list and get_count for standard DocTypes
    # if no custom logic is provided here.
    pass

@frappe.whitelist()
def get_list_data(doctype, fields, filters, sort_by, sort_order, start, page_length, as_dict=False):
    """
    This function is a custom endpoint to fetch data for the list view.
    It's not strictly necessary if the default behavior is sufficient,
    but it allows for custom data shaping.
    """
    # Ensure essential fields for formatters are included
    if isinstance(fields, list):
        if 'latitude' not in fields:
            fields.append('latitude')
        if 'longitude' not in fields:
            fields.append('longitude')
        if 'image_link' not in fields:
            fields.append('image_link')

    data = frappe.get_list(
        doctype,
        fields=fields,
        filters=filters,
        order_by=f"{sort_by} {sort_order}",
        start=start,
        page_length=page_length,
        as_list=not as_dict
    )
    frappe.log(data)
    return data