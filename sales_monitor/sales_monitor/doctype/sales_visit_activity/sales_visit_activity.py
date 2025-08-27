
# Copyright (c) 2025, [Your Name] and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class SalesVisitActivity(Document):
    def db_insert(self):
        pass

    def load_from_db(self):
        if self.name:
            data = frappe.db.get_value("Sales Activity Monitoring", self.name, "*", as_dict=True)
            if data:
                # Manually set each value to avoid triggering the complex .update() method
                for key, value in data.items():
                    self.set(key, value)

    def db_update(self):
        pass

    def delete(self):
        pass

    @staticmethod
    def get_list(filters=None, page_length=20, order_by=None, fields=None):
        
        # The doctype to query from
        source_doctype = "Sales Activity Monitoring"

        # HACK: Frappe's get_list also reads from frappe.form_dict directly.
        # If the filters from the UI are an empty list string, it causes a crash internally.
        # We will modify the form_dict in-place to prevent this.
        if frappe.form_dict.get("filters") == "[]":
            frappe.form_dict.filters = "{}"

        # Parse filters if they are a string and ensure it's a dict
        parsed_filters = {}
        if isinstance(filters, str):
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError:
                parsed_filters = {}
        elif isinstance(filters, (list, dict)):
            parsed_filters = filters

        if isinstance(parsed_filters, list) and not parsed_filters:
            parsed_filters = {}

        # Get the list of fields to fetch from the source table
        if not fields:
            meta = frappe.get_meta(source_doctype)
            fields = [df.fieldname for df in meta.fields if df.in_list_view]
            fields.extend(['name', 'latitude', 'longitude'])

        data = frappe.get_list(
            source_doctype,
            filters=parsed_filters,
            fields=list(set(fields)),
            order_by=order_by,
            limit_page_length=page_length,
            limit_start=frappe.form_dict.get('start', 0)
        )
        
        return data

    @staticmethod
    def get_count(filters=None):
        
        # Parse filters if they are a string and ensure it's a dict
        parsed_filters = {}
        if isinstance(filters, str):
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError:
                parsed_filters = {}
        elif isinstance(filters, (list, dict)):
            parsed_filters = filters

        if isinstance(parsed_filters, list) and not parsed_filters:
            parsed_filters = {}
            
        return frappe.db.count("Sales Activity Monitoring", parsed_filters)

    @staticmethod
    def get_stats(stats, name=None):
        return []
