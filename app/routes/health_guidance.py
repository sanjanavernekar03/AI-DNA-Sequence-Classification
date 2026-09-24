import json
from flask import Blueprint, render_template, request, jsonify, session
from app.routes.auth import login_required
from app.services.health_service import generate_health_guidance
from app.database.connection import get_db

health_bp = Blueprint('health_guidance', __name__, url_prefix='/health-guidance')

@health_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    guidance_result = None
    problem_input = ""
    language = "en"
    user_id = session['user_id']

    if request.method == 'POST':
        problem_input = request.form.get('health_problem', '').strip()
        language = request.form.get('language', 'en').strip()

        if problem_input:
            guidance_result = generate_health_guidance(problem_input, language=language)
            
            # Store in health_guidance_history table
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO health_guidance_history (user_id, health_problem, language, guidance_json) VALUES (%s, %s, %s, %s)",
                        (user_id, problem_input, language, json.dumps(guidance_result))
                    )
                    cursor.close()
            except Exception:
                pass

    return render_template(
        'health/guidance.html',
        guidance=guidance_result,
        problem=problem_input,
        language=language
    )


@health_bp.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    data = request.get_json() or {}
    problem = data.get('problem', '').strip()
    language = data.get('language', 'en')

    if not problem:
        return jsonify({'error': 'Please enter a health concern or problem.'}), 400

    result = generate_health_guidance(problem, language=language)
    return jsonify(result)
