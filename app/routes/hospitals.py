from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from app.routes.auth import login_required
from app.services.maps_service import geocode_address, search_nearby_hospitals
from app.services.hospital_service import save_or_get_hospital, get_hospital_by_id, get_doctors_by_hospital_id

hospitals_bp = Blueprint('hospitals', __name__, url_prefix='/hospitals')

@hospitals_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user = g.user or {}

    query_lat = request.args.get('lat') or request.form.get('lat')
    query_lng = request.args.get('lng') or request.form.get('lng')
    manual_location = (request.args.get('location') or request.form.get('location') or '').strip()

    # Registered user address fallback
    user_address_parts = [
        user.get('address'),
        user.get('city'),
        user.get('state'),
        user.get('country'),
        user.get('postal_code')
    ]
    registered_address = ", ".join([p for p in user_address_parts if p and str(p).strip()]).strip()
    user_lat = user.get('latitude')
    user_lng = user.get('longitude')

    coords = None
    search_location = ""
    location_mode = "registered"

    # Case 1: Device Geolocation (Current Location)
    if query_lat and query_lng:
        try:
            coords = {'lat': float(query_lat), 'lng': float(query_lng)}
            location_mode = "current"
            search_location = "Current Device Location"
        except (ValueError, TypeError):
            coords = None

    # Case 2: Manual Location Search
    if not coords and manual_location and manual_location.lower() != registered_address.lower():
        coords = geocode_address(manual_location)
        if coords:
            location_mode = "manual"
            search_location = manual_location
        else:
            flash(f"Unable to find location for '{manual_location}'. Please try another location.", "warning")

    # Case 3: Registered Address (Default Fallback)
    if not coords:
        location_mode = "registered"
        if user_lat and user_lng:
            try:
                coords = {'lat': float(user_lat), 'lng': float(user_lng)}
                search_location = registered_address or "Registered Location"
            except (ValueError, TypeError):
                coords = None

        if not coords and registered_address:
            coords = geocode_address(registered_address)
            if coords:
                search_location = registered_address

        if not coords and user.get('city'):
            coords = geocode_address(user.get('city'))
            if coords:
                search_location = user.get('city')

    nearby_hospitals_data = []
    if coords:
        try:
            nearby_hospitals_data = search_nearby_hospitals(coords['lat'], coords['lng'])
        except Exception as exc:
            nearby_hospitals_data = []
            flash("Hospital lookup service is currently busy. Please try again or search a nearby city.", "info")

    hospitals_list = []
    for h_data in nearby_hospitals_data:
        h_data['city'] = user.get('city', '')
        h_data['state'] = user.get('state', '')
        h_data['country'] = user.get('country', '')
        h_data['postal_code'] = user.get('postal_code', '')
        try:
            db_id = save_or_get_hospital(h_data)
            h_data['db_id'] = db_id
        except Exception:
            h_data['db_id'] = 1
        hospitals_list.append(h_data)

    display_search_location = search_location or registered_address or "Registered Location"

    return render_template(
        'hospitals/hospitals.html',
        hospitals=hospitals_list,
        search_location=display_search_location,
        registered_address=registered_address,
        user_coords=coords,
        location_mode=location_mode
    )


@hospitals_bp.route('/api/search', methods=['POST'])
@login_required
def search_api():
    payload = request.get_json(silent=True) or {}
    lat = payload.get('lat')
    lng = payload.get('lng')
    location = (payload.get('location') or '').strip()

    if lat is None or lng is None:
        coords = geocode_address(location)
    else:
        try:
            coords = {'lat': float(lat), 'lng': float(lng)}
        except (TypeError, ValueError):
            coords = None

    if not coords:
        return jsonify({'error': 'Enable location access or add a valid address to find nearby hospitals.'}), 400

    hospitals_data = search_nearby_hospitals(coords['lat'], coords['lng'])
    hospitals_list = []
    user = g.user or {}
    for hospital_data in hospitals_data:
        hospital_data.update({
            'city': user.get('city', ''),
            'state': user.get('state', ''),
            'country': user.get('country', ''),
            'postal_code': user.get('postal_code', ''),
        })
        hospital_data['db_id'] = save_or_get_hospital(hospital_data)
        hospitals_list.append(hospital_data)

    return jsonify({'user_coords': coords, 'hospitals': hospitals_list})


@hospitals_bp.route('/<int:hospital_id>/doctors')
@login_required
def doctors(hospital_id: int):
    hospital = get_hospital_by_id(hospital_id)
    if not hospital:
        flash("Hospital not found.", "danger")
        return redirect(url_for('hospitals.index'))

    doctors_list = get_doctors_by_hospital_id(hospital_id)
    return render_template(
        'hospitals/doctors.html',
        hospital=hospital,
        doctors=doctors_list
    )
