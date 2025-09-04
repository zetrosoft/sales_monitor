# # Copyright (c) 2025, [Your Name] and contributors
# # For license information, please see license.txt
# 
# import frappe
# import json
# from frappe.model.document import Document
# 
# class SalesVisitActivity(Document):
#     def db_insert(self):
#         pass
# 
#     def load_from_db(self):
#         if self.name:
#             data = frappe.db.get_value("Sales Activity Monitoring", self.name, "*", as_dict=True)
#             if data:
#                 # Manually set each value to avoid triggering the complex .update() method
#                 for key, value in data.items():
#                     self.set(key, value)
# 
#     def db_update(self):
#         pass
# 
#     def delete(self):
#         pass
# 
#     @staticmethod
#     def get_list(filters=None, page_length=20, order_by=None, fields=None):
#         
#         # For virtual doctypes, get_list is called with a single dict argument
#         # We need to extract the actual arguments from it.
#         if isinstance(filters, dict) and "doctype" in filters:
#             args = filters
#             filters = args.get("filters")
#             page_length = args.get("page_length") or args.get("limit_page_length") or page_length
#             order_by = args.get("order_by") or order_by
#             fields = args.get("fields") or fields
# 
#         # The doctype to query from
#         source_doctype = "Sales Activity Monitoring"
# 
#         # HACK: Frappe's get_list also reads from frappe.form_dict directly.
#         # If the filters from the UI are an empty list string, it causes a crash internally.
#         # We will modify the form_dict in-place to prevent this.
#         if frappe.form_dict.get("filters") == "[]":
#             frappe.form_dict.filters = "{}"
# 
#         # Parse filters if they are a string and ensure it's a dict
#         parsed_filters = {}
#         if isinstance(filters, str):
#             try:
#                 parsed_filters = json.loads(filters)
#             except json.JSONDecodeError:
#                 parsed_filters = {}
#         elif isinstance(filters, (list, dict)):
#             parsed_filters = filters
# 
#         if isinstance(parsed_filters, list) and not parsed_filters:
#             parsed_filters = {}
# 
#         # Parse fields if they are a string
#         parsed_fields = fields
#         if isinstance(fields, str):
#             try:
#                 parsed_fields = json.loads(fields)
#             except json.JSONDecodeError:
#                 pass # Not a JSON string, assume single field or comma-separated
# 
#         # Get the list of fields to fetch from the source table
#         if not parsed_fields:
#             meta = frappe.get_meta(source_doctype)
#             parsed_fields = [df.fieldname for df in meta.fields if df.in_list_view]
#             parsed_fields.extend(['name', 'latitude', 'longitude'])
# 
#         data = frappe.get_list(
#             source_doctype,
#             filters=parsed_filters,
#             fields=list(set(parsed_fields)),
#             order_by=order_by,
#             limit_page_length=page_length,
#             limit_start=frappe.form_dict.get('start', 0)
#         )
#         
#         return data
# 
#     @staticmethod
#     def get_count(filters=None):
#         
#         actual_filters = filters
#         if isinstance(filters, dict) and "filters" in filters:
#             actual_filters = filters["filters"]
# 
#         # Parse filters if they are a string and ensure it's a dict
#         parsed_filters = {}
#         if isinstance(actual_filters, str):
#             try:
#                 parsed_filters = json.loads(actual_filters)
#             except json.JSONDecodeError:
#                 parsed_filters = {}
#         elif isinstance(actual_filters, (list, dict)):
#             parsed_filters = actual_filters
# 
#         if isinstance(parsed_filters, list) and not parsed_filters:
#             parsed_filters = {}
#             
#         return frappe.db.count("Sales Activity Monitoring", parsed_filters)
# 
#     @staticmethod
#     def get_stats(stats, name=None):
#         return []