from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from app.routes.auth import login_required
from app.services.maps_service import geocode_address, reverse_geocode, search_nearby_hospitals
from app.services.hospital_service import save_or_get_hospitals_batch, save_or_get_hospital, get_hospital_by_id, get_doctors_by_hospital_id

hospitals_bp = Blueprint('hospitals', __name__, url_prefix='/hospitals')

@hospitals_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user = g.user or {}

    query_lat = request.args.get('lat') or request.form.get('lat')
    query_lng = request.args.get('lng') or request.form.get('lng')
    manual_location = (request.args.get('location') or request.form.get('location') or '').strip()
    mode_param = (request.args.get('mode') or request.form.get('mode') or '').strip()

    # Registered user address
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

    # MODE 1: Explicit GPS Current Location (via lat & lng query params or mode=current)
    if (query_lat and query_lng and mode_param != "registered" and not manual_location) or mode_param == "current":
        if query_lat and query_lng:
            try:
                coords = {'lat': float(query_lat), 'lng': float(query_lng)}
                location_mode = "current"
                # Reverse geocode exact GPS coordinates to obtain actual location name/address
                geo_name = reverse_geocode(coords['lat'], coords['lng'])
                if geo_name:
                    search_location = geo_name
                else:
                    search_location = f"Current Location ({coords['lat']:.4f}, {coords['lng']:.4f})"
            except (ValueError, TypeError):
                coords = None

    # MODE 3: Manual Address Search
    if not coords and manual_location:
        coords = geocode_address(manual_location)
        if coords:
            location_mode = "manual"
            search_location = manual_location
        else:
            flash(f"Unable to find location for '{manual_location}'. Please check the address.", "warning")

    # MODE 2: Registered Address Search (Used if mode=registered OR default if no current coords or manual location)
    if not coords and (mode_param == "registered" or not manual_location):
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

        if not coords:
            search_location = registered_address or user.get('city') or ""

    nearby_hospitals_data = []
    if coords:
        try:
            nearby_hospitals_data = search_nearby_hospitals(coords['lat'], coords['lng'])
        except Exception as exc:
            nearby_hospitals_data = []
            flash("Hospital lookup service is currently busy. Please try again or search a nearby city.", "info")

    for h_data in nearby_hospitals_data:
        h_data['city'] = user.get('city', '')
        h_data['state'] = user.get('state', '')
        h_data['country'] = user.get('country', '')
        h_data['postal_code'] = user.get('postal_code', '')

    hospitals_list = save_or_get_hospitals_batch(nearby_hospitals_data)
    display_search_location = search_location or registered_address or ""

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
    mode_param = (payload.get('mode') or '').strip()

    coords = None
    location_mode = mode_param or "manual"
    user = g.user or {}

    if lat is not None and lng is not None:
        try:
            coords = {'lat': float(lat), 'lng': float(lng)}
            if not mode_param:
                location_mode = "current"
        except (TypeError, ValueError):
            coords = None

    if not coords and location:
        coords = geocode_address(location)
        location_mode = "manual"

    if not coords and mode_param == "registered":
        user_lat = user.get('latitude')
        user_lng = user.get('longitude')
        if user_lat and user_lng:
            try:
                coords = {'lat': float(user_lat), 'lng': float(user_lng)}
            except (TypeError, ValueError):
                coords = None

    if not coords:
        return jsonify({'error': 'Enable location access or add a valid address to find nearby hospitals.'}), 400

    display_name = ""
    if lat is not None and lng is not None:
        display_name = reverse_geocode(coords['lat'], coords['lng']) or f"Current Location ({coords['lat']:.4f}, {coords['lng']:.4f})"
    else:
        display_name = location or "Registered Location"

    hospitals_data = search_nearby_hospitals(coords['lat'], coords['lng'])
    for hospital_data in hospitals_data:
        hospital_data.update({
            'city': user.get('city', ''),
            'state': user.get('state', ''),
            'country': user.get('country', ''),
            'postal_code': user.get('postal_code', ''),
        })

    hospitals_list = save_or_get_hospitals_batch(hospitals_data)

    return jsonify({
        'user_coords': coords,
        'search_location': display_name,
        'hospitals': hospitals_list,
        'location_mode': location_mode
    })


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

