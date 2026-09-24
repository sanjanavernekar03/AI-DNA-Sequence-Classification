from flask import Blueprint, request, jsonify, session
from app.routes.auth import login_required
from app.services.chatbot_service import ChatbotServiceError, get_chatbot_response
from app.database.connection import get_db

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    current_page = data.get('current_page', '')
    language = data.get('language', 'en')
    conversation = data.get('conversation', [])
    user_id = session.get('user_id')

    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    if not isinstance(conversation, list):
        return jsonify({'error': 'Conversation history must be a list.'}), 400

    try:
        result = get_chatbot_response(
            user_message,
            current_page=current_page,
            language=language,
            conversation=conversation,
        )
    except ChatbotServiceError as exc:
        return jsonify({'error': str(exc)}), 503

    result.pop('disclaimer', None)

    # Save to chat_history table
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_id, user_message, bot_response) VALUES (%s, %s, %s)",
                (user_id, user_message, result['response'])
            )
            cursor.close()
    except Exception:
        pass

    return jsonify(result)
