from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.routes.auth import login_required
from app.services.hospital_service import get_hospital_by_id, get_doctors_by_hospital_id
from app.services.booking_service import create_appointment, get_user_appointments, cancel_user_appointment

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    user_id = session['user_id']
    user = g.user or {}

    hospital_id = request.args.get('hospital_id', type=int) or request.form.get('hospital_id', type=int)
    doctor_id = request.args.get('doctor_id', type=int) or request.form.get('doctor_id', type=int)

    hospital = get_hospital_by_id(hospital_id) if hospital_id else None
    doctor = None
    docs = []

    if hospital_id:
        docs = get_doctors_by_hospital_id(hospital_id)
        if doctor_id:
            doctor = next((d for d in docs if d['id'] == doctor_id), None)

    if request.method == 'POST':
        selected_hosp_id = int(request.form.get('hospital_id'))
        selected_doc_id = int(request.form.get('doctor_id'))
        appointment_date = request.form.get('appointment_date', '').strip()
        appointment_time = request.form.get('appointment_time', '').strip()
        reason_for_visit = request.form.get('reason_for_visit', '').strip()
        patient_name = request.form.get('patient_name', '').strip()
        phone = request.form.get('phone', '').strip()
        patient_email = request.form.get('patient_email', '').strip() or user.get('email', '')
        notes = request.form.get('notes', '').strip()

        result = create_appointment(
            user_id=user_id,
            hospital_id=selected_hosp_id,
            doctor_id=selected_doc_id,
            appointment_date_str=appointment_date,
            appointment_time=appointment_time,
            reason_for_visit=reason_for_visit,
            patient_name=patient_name,
            phone=phone,
            patient_email=patient_email,
            notes=notes
        )

        if result['success']:
            flash("Appointment Confirmed Successfully!", "success")
            return redirect(url_for('appointments.my_appointments'))
        else:
            flash(f"Booking Error: {result['error']}", "danger")

    return render_template(
        'appointments/booking.html',
        hospital=hospital,
        doctor=doctor,
        doctors=docs,
        user=user
    )


@appointments_bp.route('/my-appointments')
@login_required
def my_appointments():
    user_id = session['user_id']
    appts = get_user_appointments(user_id)
    return render_template('appointments/my_appointments.html', appointments=appts)


@appointments_bp.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel(appointment_id: int):
    user_id = session['user_id']
    success = cancel_user_appointment(appointment_id, user_id)
    if success:
        flash("Appointment has been cancelled.", "info")
    else:
        flash("Unable to cancel appointment.", "danger")
    return redirect(url_for('appointments.my_appointments'))

