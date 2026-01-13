import frappe


@frappe.whitelist()
def create_address_from_map(customer_name, address_title, address_line1, address_line2, latitude, longitude, city, state, pincode, country):
    """
    Membuat Address DocType baru berdasarkan lokasi yang dipilih di peta.
    Menerima data alamat terstruktur (city, state, pincode, country) untuk memenuhi
    persyaratan field wajib pada DocType Address.
    """
    # Menambahkan validasi untuk field baru yang wajib, khususnya City dan Country.
    if not customer_name or not address_title or not address_line1 or latitude is None or longitude is None or not city or not country:
        frappe.throw(frappe._("Missing required address details (Customer Name, Title, Address Line 1, Location, City, or Country)."))

    try:
        # Buat DocType Address baru
        address = frappe.new_doc("Address")
        address.address_title = address_title
        address.address_type = "Billing" # Atau jenis lain yang sesuai
        address.address_line1 = address_line1
        address.address_line2 = address_line2 # Tambahkan address_line2

        # --- ASSIGN FIELD ALAMAT TERSTRUKTUR DARI MAP ---
        address.city = city
        address.state = state
        address.pincode = pincode
        address.country = country
        address.custom_latitude = latitude
        address.custom_longitude = longitude
        # ----------------------------------------------------

        # Hubungkan Address ke Customer
        address.append("links", {
            "link_doctype": "Customer",
            "link_name": customer_name
        })

        address.save(ignore_permissions=True)
        frappe.db.commit()
        return address.name

    except Exception as e:
        # Log error untuk memudahkan debugging di sisi server
        frappe.log_error(frappe.get_traceback(), "create_address_from_map Error")
        frappe.throw(frappe._(f"Error creating address: {e}"))
