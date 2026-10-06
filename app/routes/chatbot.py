from flask import Blueprint, request, jsonify, session, g
from app.routes.auth import login_required
from app.services.chatbot_service import ChatbotServiceError, get_chatbot_response
from app.services.recommendation_service import get_ai_recommendation
from app.services.voice_assistant_service import process_voice_assistant_command
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
    user_location = data.get('user_location')
    user_id = session.get('user_id')
    user_info = getattr(g, 'user', None) or {}

    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    if not isinstance(conversation, list):
        return jsonify({'error': 'Conversation history must be a list.'}), 400

    # 1. Try AI Hospital & Doctor Recommendation
    rec_result = get_ai_recommendation(
        user_message,
        language=language,
        user_location=user_location,
        user_info=user_info
    )

    if rec_result:
        result = {
            'response': rec_result['response'],
            'intent': 'FIND_HOSPITAL',
            'action': 'SHOW_RECOMMENDATION',
            'language': language
        }
    else:
        # 2. Try Controlled Voice Intent (Navigation, Analysis Run, Confirmation)
        voice_res = process_voice_assistant_command(
            message=user_message,
            current_page=current_page,
            language=language,
            user_location=user_location,
            user_info=user_info,
            conversation=conversation,
            pending_action=data.get('pending_action')
        )

        if voice_res and voice_res.get('intent') != 'CHATBOT_QUERY':
            result = voice_res
        else:
            # 3. Informational Query via Local Ollama Model
            try:
                cb_res = get_chatbot_response(
                    user_message,
                    current_page=current_page,
                    language=language,
                    conversation=conversation,
                )
                result = {
                    'response': cb_res['response'],
                    'intent': 'CHATBOT_QUERY',
                    'action': 'CHATBOT',
                    'language': language
                }
            except ChatbotServiceError as exc:
                return jsonify({'error': str(exc)}), 503

    # Save to chat_history table
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_id, user_message, bot_response) VALUES (%s, %s, %s)",
                (user_id, user_message, result.get('response', ''))
            )
            cursor.close()
    except Exception:
        pass

    return jsonify(result)


@chatbot_bp.route('/voice-command', methods=['POST'])
@login_required
def voice_command():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    current_page = data.get('current_page', '')
    language = data.get('language', 'en')
    conversation = data.get('conversation', [])
    user_location = data.get('user_location')
    user_id = session.get('user_id')
    user_info = getattr(g, 'user', None) or {}

    if not user_message:
        return jsonify({'error': 'Speech input cannot be empty'}), 400

    result = process_voice_assistant_command(
        message=user_message,
        current_page=current_page,
        language=language,
        user_location=user_location,
        user_info=user_info,
        conversation=conversation,
        pending_action=data.get('pending_action')
    )

    return jsonify(result)


