from flask import Blueprint, render_template, request, session
from app.routes.auth import login_required
from app.database.queries import get_user_combined_history

history_bp = Blueprint('history', __name__, url_prefix='/history')


@history_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    history_items = get_user_combined_history(user_id, limit=100)

    # Optional filter by module_type
    filter_type = request.args.get('type', 'all')
    search_query = request.args.get('q', '').strip().lower()

    filtered = []
    for item in history_items:
        if filter_type != 'all' and item['module_type'] != filter_type:
            continue
        if search_query:
            text_corpus = f"{item['sequence_name']} {item['module_name']} {item.get('classification_result', '')} {item.get('disease_prediction', '')}".lower()
            if search_query not in text_corpus:
                continue
        filtered.append(item)

    return render_template(
        'history/index.html',
        history=filtered,
        filter_type=filter_type,
        search_query=search_query
    )
