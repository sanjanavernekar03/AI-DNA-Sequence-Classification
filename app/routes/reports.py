import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, send_file, abort
from app.routes.auth import login_required
from app.database.queries import (
    get_user_reports, get_report_by_uuid, get_report_by_id, delete_report,
    get_sequence_analysis_by_id, get_similarity_analysis_by_id,
    get_mutation_analysis_by_id, get_mutations_by_analysis_id,
    get_classification_by_id, get_disease_prediction_by_id,
    get_visualization_by_id, get_complete_analysis_by_id
)
from app.services.report_service import generate_and_store_report

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    user_reports = get_user_reports(user_id)
    return render_template('reports/index.html', reports=user_reports)


@reports_bp.route('/generate/<analysis_type>/<int:analysis_id>')
@login_required
def generate(analysis_type: str, analysis_id: int):
    user_id = session['user_id']
    user_name = session.get('full_name', 'Researcher')

    # Fetch corresponding analysis data
    data = None
    if analysis_type == 'sequence':
        data = get_sequence_analysis_by_id(analysis_id, user_id)
    elif analysis_type == 'similarity':
        data = get_similarity_analysis_by_id(analysis_id, user_id)
    elif analysis_type == 'mutation':
        data = get_mutation_analysis_by_id(analysis_id, user_id)
        if data:
            data['mutations_list'] = get_mutations_by_analysis_id(analysis_id, user_id)
    elif analysis_type == 'classification':
        data = get_classification_by_id(analysis_id, user_id)
    elif analysis_type == 'disease':
        data = get_disease_prediction_by_id(analysis_id, user_id)
    elif analysis_type == 'visualization':
        vis = get_visualization_by_id(analysis_id, user_id)
        data = vis.get('chart_config', {}) if vis else None
        if data:
            data['id'] = analysis_id
    elif analysis_type == 'complete':
        data = get_complete_analysis_by_id(analysis_id, user_id)

    if not data:
        flash(f"Could not locate {analysis_type} analysis record #{analysis_id}.", "danger")
        return redirect(url_for('reports.index'))

    try:
        report_record = generate_and_store_report(
            user_id=user_id,
            user_name=user_name,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
            data=data
        )
        flash(f"PDF Report generated successfully! [{report_record['file_name']}]", "success")
        return redirect(url_for('reports.download', report_uuid=report_record['report_uuid']))
    except Exception as e:
        flash(f"Error generating PDF report: {str(e)}", "danger")
        return redirect(url_for('reports.index'))


@reports_bp.route('/download/<report_uuid>')
@login_required
def download(report_uuid: str):
    user_id = session['user_id']
    report = get_report_by_uuid(report_uuid, user_id)
    if not report or not os.path.exists(report['file_path']):
        flash("Report file not found or unauthorized access.", "danger")
        return redirect(url_for('reports.index'))

    return send_file(
        report['file_path'],
        as_attachment=True,
        download_name=report['file_name'],
        mimetype='application/pdf'
    )


@reports_bp.route('/view/<report_uuid>')
@login_required
def view_pdf(report_uuid: str):
    user_id = session['user_id']
    report = get_report_by_uuid(report_uuid, user_id)
    if not report or not os.path.exists(report['file_path']):
        flash("Report file not found or access denied.", "danger")
        return redirect(url_for('reports.index'))

    return send_file(
        report['file_path'],
        as_attachment=False,
        mimetype='application/pdf'
    )


@reports_bp.route('/delete/<int:report_id>', methods=['POST'])
@login_required
def delete(report_id: int):
    user_id = session['user_id']
    report = delete_report(report_id, user_id)
    if report and os.path.exists(report.get('file_path', '')):
        try:
            os.remove(report['file_path'])
        except Exception:
            pass
    flash("Report deleted successfully.", "info")
    return redirect(url_for('reports.index'))
