import functools
import re
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.connection import get_db
from app.database.queries import (
    create_user,
    get_user_by_username_or_email,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    update_user_profile,
    update_user_password
)

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    """Decorator to require login for protected routes."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this genomic module.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return view(**kwargs)
    return wrapped_view


@auth_bp.before_app_request
def load_logged_in_user():
    """Load user dict into Flask `g.user` if session exists."""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        try:
            g.user = get_user_by_id(user_id)
            if g.user and not session.get('admin_id'):
                # Track user activity
                try:
                    with get_db() as db:
                        cur = db.cursor()
                        cur.execute("UPDATE users SET last_activity_at=CURRENT_TIMESTAMP WHERE id=%s", (user_id,))
                        db.commit() if hasattr(db, 'commit') else None
                        cur.close()
                except Exception as e:
                    pass
        except Exception:
            g.user = None


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        # Step 1: Account Credentials
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Step 1: Personal Details
        full_name = request.form.get('full_name', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip() or None
        gender = request.form.get('gender', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        address = request.form.get('address', '').strip() or None
        city = request.form.get('city', '').strip() or None
        state = request.form.get('state', '').strip() or None
        country = request.form.get('country', '').strip() or None
        postal_code = request.form.get('postal_code', '').strip() or None

        # Step 2: Health Information
        blood_group = request.form.get('blood_group', '').strip() or None
        height = request.form.get('height', '').strip() or None
        weight = request.form.get('weight', '').strip() or None
        
        # Parse numeric height/weight safely
        try:
            height = float(height) if height else None
        except ValueError:
            height = None
        try:
            weight = float(weight) if weight else None
        except ValueError:
            weight = None

        # Server-Side Step 1 Validation
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash("Please enter a valid email address.", "danger")
            return render_template('auth/register.html', form_data=request.form)

        if not username or len(username) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash("Username must be at least 3 alphanumeric characters.", "danger")
            return render_template('auth/register.html', form_data=request.form)

        if not password or len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return render_template('auth/register.html', form_data=request.form)

        if password != confirm_password:
            flash("Passwords do not match. Please verify.", "danger")
            return render_template('auth/register.html', form_data=request.form)

        # Server-Side Step 2 Validation
        if not full_name:
            flash("Please provide your Full Name.", "danger")
            return render_template('auth/register.html', form_data=request.form)

        # Uniqueness Verification
        try:
            if get_user_by_username(username):
                flash("This username is already taken. Please choose another.", "danger")
                return render_template('auth/register.html', form_data=request.form)

            if get_user_by_email(email):
                flash("An account with this email address already exists. Please sign in.", "danger")
                return render_template('auth/register.html', form_data=request.form)

            from app.services.maps_service import geocode_address
            user_address_parts = [address, city, state, country, postal_code]
            full_address_str = ", ".join([p for p in user_address_parts if p and p.strip()])
            coords = geocode_address(full_address_str) if full_address_str else None
            user_lat = coords['lat'] if coords else None
            user_lng = coords['lng'] if coords else None

            password_hash = generate_password_hash(password)
            user_id = create_user(
                full_name=full_name,
                email=email,
                username=username,
                password_hash=password_hash,
                role='researcher',
                date_of_birth=date_of_birth,
                gender=gender,
                phone=phone,
                country=country,
                state=state,
                city=city,
                address=address,
                postal_code=postal_code,
                blood_group=blood_group,
                height=height,
                weight=weight,
                latitude=user_lat,
                longitude=user_lng
            )
            print(f"DEBUG: Created user with ID {user_id}")
            flash("Account Created Successfully! Please log in to your account.", "success")
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f"Unable to complete registration: {str(e)}", "danger")
            return render_template('auth/register.html', form_data=request.form)

    return render_template('auth/register.html', form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('auth/login.html', identifier=identifier)

        try:
            user = get_user_by_username_or_email(identifier)
            is_admin_table = False

            if not user:
                # Fallback to check admin_users table
                with get_db() as db:
                    cur = db.cursor(dictionary=True)
                    cur.execute("SELECT id, username, display_name as full_name, password_hash, is_active FROM admin_users WHERE username = %s", (identifier,))
                    admin = cur.fetchone()
                    cur.close()
                if admin:
                    user = admin
                    user['role'] = 'admin'
                    user['email'] = f"{admin['username']}@system.local" # Dummy email for session
                    is_admin_table = True

            is_valid = False
            if user and not user.get('is_active', 1):
                flash("This account has been deactivated. Please contact the administrator.", "danger")
                return render_template('auth/login.html', identifier=identifier)

            if user:
                print(f"DEBUG: password='{password}', hash='{user['password_hash']}'")
                is_valid = check_password_hash(user['password_hash'], password) or check_password_hash(user['password_hash'], password.strip())
                print(f"DEBUG LOGIN: user={user['username']}, is_valid={is_valid}")

            if user and is_valid:
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                session['email'] = user.get('email', '')
                session['role'] = user.get('role', 'researcher')
                
                if is_admin_table:
                    session['admin_id'] = user['id']
                    session['admin_username'] = user['username']
                    session['admin_name'] = user['full_name']
                    try:
                        with get_db() as db:
                            cur = db.cursor()
                            cur.execute("UPDATE admin_users SET last_login_at=CURRENT_TIMESTAMP WHERE id=%s", (user['id'],))
                            db.commit() if hasattr(db, 'commit') else None
                            cur.close()
                    except Exception as db_e:
                        logger.error(f"Failed to update admin login time: {db_e}")
                else:
                    try:
                        with get_db() as db:
                            cur = db.cursor()
                            cur.execute("UPDATE users SET updated_at=CURRENT_TIMESTAMP, last_login_at=CURRENT_TIMESTAMP WHERE id=%s", (user['id'],))
                            db.commit() if hasattr(db, 'commit') else None
                            cur.close()
                    except Exception as db_e:
                        logger.error(f"Failed to update user login time: {db_e}")

                if remember:
                    session.permanent = True

                logger.info(f"Successful login for user: {user['username']}")
                flash(f"Welcome back, {user['full_name']}!", "success")
                
                if session['role'] == 'admin':
                    return redirect(url_for('admin.dashboard'))
                next_url = request.args.get('next')
                if next_url and next_url.startswith('/') and next_url != '/None':
                    return redirect(next_url)
                return redirect(url_for('dashboard.index'))
            else:
                if not user:
                    logger.warning(f"Login failed: User '{identifier}' not found in database.")
                else:
                    logger.warning(f"Login failed: Incorrect password for user '{identifier}'.")
                flash("Invalid username/email or password.", "danger")
                return render_template('auth/login.html', identifier=identifier)

        except Exception as e:
            logger.error(f"Database error during login: {e}")
            flash("Unable to access the database. Please try again.", "danger")
            return render_template('auth/login.html', identifier=identifier)

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    user = get_user_by_id(user_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            blood_group = request.form.get('blood_group', '').strip() or None
            height = request.form.get('height', '').strip() or None
            weight = request.form.get('weight', '').strip() or None

            try:
                height = float(height) if height else None
            except ValueError:
                height = None
            try:
                weight = float(weight) if weight else None
            except ValueError:
                weight = None

            if not full_name or not email:
                flash("Full name and email are required.", "danger")
            else:
                try:
                    from app.services.maps_service import geocode_address
                    lat = None
                    lng = None
                    if address:
                        coords = geocode_address(address)
                        if coords:
                            lat = coords['lat']
                            lng = coords['lng']
                            
                    update_user_profile(user_id, full_name, email, phone=phone, address=address, latitude=lat, longitude=lng, blood_group=blood_group, height=height, weight=weight)
                    session['full_name'] = full_name
                    session['email'] = email
                    flash("Profile updated successfully.", "success")
                    return redirect(url_for('auth.profile'))
                except Exception as e:
                    flash(f"Error updating profile: {str(e)}", "danger")

        elif action == 'change_password':
            curr_pass = request.form.get('current_password', '')
            new_pass = request.form.get('new_password', '')
            confirm_pass = request.form.get('confirm_password', '')

            if not check_password_hash(user['password_hash'], curr_pass):
                flash("Current password is incorrect.", "danger")
            elif len(new_pass) < 8:
                flash("New password must be at least 8 characters long.", "danger")
            elif new_pass != confirm_pass:
                flash("New passwords do not match.", "danger")
            else:
                try:
                    new_hash = generate_password_hash(new_pass)
                    update_user_password(user_id, new_hash)
                    flash("Password changed successfully.", "success")
                    return redirect(url_for('auth.profile'))
                except Exception as e:
                    flash(f"Error changing password: {str(e)}", "danger")

    return render_template('auth/profile.html', user=user)
