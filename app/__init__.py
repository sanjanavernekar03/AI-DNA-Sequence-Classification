import os
import logging
from flask import Flask, render_template, session, redirect, url_for
from app.config import Config
from app.database.connection import init_connection_pool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logging.getLogger("mysql.connector").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize MySQL Connection Pool
    with app.app_context():
        try:
            init_connection_pool()
        except Exception as e:
            logger.warning(f"Database connection initialization deferred: {e}")

    # Register Blueprints
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.sequence import sequence_bp
    from app.routes.similarity import similarity_bp
    from app.routes.mutation import mutation_bp
    from app.routes.classification import classification_bp
    from app.routes.disease import disease_bp
    from app.routes.visualization import visualization_bp
    from app.routes.complete_analysis import complete_bp
    from app.routes.reports import reports_bp
    from app.routes.history import history_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.hospitals import hospitals_bp
    from app.routes.appointments import appointments_bp
    from app.routes.health_guidance import health_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(sequence_bp)
    app.register_blueprint(similarity_bp)
    app.register_blueprint(mutation_bp)
    app.register_blueprint(classification_bp)
    app.register_blueprint(disease_bp)
    app.register_blueprint(visualization_bp)
    app.register_blueprint(complete_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(hospitals_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(health_bp)

    # Landing / Welcome Page
    @app.route('/')
    def welcome():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('welcome.html')

    # Custom Jinja Template Filters
    @app.template_filter('format_datetime')
    def format_datetime(value, fmt='%b %d, %Y %I:%M %p'):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                import datetime
                dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.strftime(fmt)
            except Exception:
                return value
        return value.strftime(fmt)

    @app.template_filter('format_bytes')
    def format_bytes(size):
        if not size:
            return "0 B"
        power = 2**10
        n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return f"{size:.1f} {power_labels[n]}B"

    # Context Processors
    @app.context_processor
    def inject_global_vars():
        import datetime
        return {
            'app_name': 'DNAura',
            'app_tagline': 'AI-Powered DNA Sequence Classification & Prediction System',
            'now_date': datetime.date.today().isoformat(),
            'current_user': {
                'is_authenticated': 'user_id' in session,
                'id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name'),
                'email': session.get('email')
            }
        }

    @app.context_processor
    def inject_admin_vars():
        return {
            'admin_authenticated': bool(session.get('admin_id')),
            'admin_name': session.get('admin_name', 'Miss Admin'),
            'admin_username': session.get('admin_username', '')
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/500.html', error_msg="Uploaded file exceeds the maximum allowed limit (16MB)."), 413

    return app
