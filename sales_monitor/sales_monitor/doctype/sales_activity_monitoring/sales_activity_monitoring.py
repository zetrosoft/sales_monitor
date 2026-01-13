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

@frappe.whitelist()
def get_customer_address(customer_name):
    if not customer_name:
        return ""

    # Find address names linked to this customer, prioritize primary
    # This correctly queries the linking table `tabDynamic Link`
    address_names = frappe.db.sql_list("""
        SELECT T1.parent
        FROM `tabDynamic Link` AS T1
        INNER JOIN `tabAddress` AS T2 ON T1.parent = T2.name
        WHERE T1.link_doctype = 'Customer' AND T1.link_name = %(customer_name)s
        ORDER BY T2.is_primary_address DESC
    """, {"customer_name": customer_name})

    if not address_names:
        return '<div class="control-value" style="padding-top: 5px; color: #888;">No address found for this customer.</div>'

    # Fetch details of the first address found (which is the primary, if available)
    address_details = frappe.get_value(
        "Address",
        address_names[0],
        ["address_line1", "address_line2", "city", "state", "pincode"],
        as_dict=True
    )

    if not address_details:
        return '<div class="control-value" style="padding-top: 5px; color: #888;">Could not fetch address details.</div>'

    # Build HTML string
    address_parts = [
        address_details.get("address_line1"),
        address_details.get("address_line2"),
        f'{address_details.get("city", "")} {address_details.get("state", "")} {address_details.get("pincode", "")}'.strip()
    ]

    html = '<div class="control-value" style="padding-top: 5px;">'
    html += '<br>'.join(filter(None, address_parts))
    html += '</div>'

    return html
