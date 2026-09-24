import json
from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash
from app.database.connection import get_db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            if request.path != "/admin":
                flash("Administrator authentication is required.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _one(sql, params=()):
    with get_db() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row


def _all(sql, params=()):
    with get_db() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows


def _log(action, target_type=None, target_id=None, details=None):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO admin_activity_logs
               (admin_id, action, target_type, target_id, details, ip_address)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (session.get("admin_id"), action, target_type, target_id, details, request.remote_addr)
        )
        cur.close()


@admin_bp.context_processor
def inject_admin_theme():
    try:
        row = _one("SELECT setting_value FROM admin_settings WHERE setting_key='theme'")
        return {"theme": row["setting_value"] if row else "dark"}
    except Exception:
        return {"theme": "dark"}



@admin_bp.route("", methods=["GET", "POST"])
def login():
    if session.get("role") == "admin":
        return redirect(url_for("admin.dashboard"))
    flash("Please login using the standard login page.", "info")
    return redirect(url_for("auth.login", next=request.args.get("next")))


@admin_bp.route("/logout")
def logout():
    admin_id = session.get("admin_id")
    if admin_id:
        _log("Admin logout", "admin", admin_id, "Administrator signed out")
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    session.pop("admin_name", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {
        "users": _one("SELECT COUNT(*) AS c FROM users")["c"],
        "active_users": _one("SELECT COUNT(*) AS c FROM users")["c"],
        "sequences": _one("SELECT COUNT(*) AS c FROM dna_sequences")["c"],
        "analyses": _one("""SELECT
            (SELECT COUNT(*) FROM sequence_analysis) +
            (SELECT COUNT(*) FROM similarity_analysis) +
            (SELECT COUNT(*) FROM mutation_analyses) +
            (SELECT COUNT(*) FROM classification_results) +
            (SELECT COUNT(*) FROM disease_predictions) +
            (SELECT COUNT(*) FROM complete_analyses) AS c""")["c"],
        "predictions": _one("""SELECT
            (SELECT COUNT(*) FROM classification_results) +
            (SELECT COUNT(*) FROM disease_predictions) AS c""")["c"],
        "mutation_analyses": _one("SELECT COUNT(*) AS c FROM mutation_analyses")["c"],
        "high_risk": _one("SELECT COUNT(*) AS c FROM disease_predictions WHERE LOWER(risk_category) IN ('high','elevated')")["c"],
        "reports": _one("SELECT COUNT(*) AS c FROM reports")["c"],
        "chatbot_conversations": _one("SELECT COUNT(*) AS c FROM chat_history")["c"],
    }

    recent_users = _all("""SELECT id, full_name, username, email, role, created_at
                           FROM users ORDER BY created_at DESC LIMIT 8""")
    recent_activity = _all("""SELECT l.*, a.username AS admin_username
                              FROM admin_activity_logs l
                              LEFT JOIN admin_users a ON a.id=l.admin_id
                              ORDER BY l.created_at DESC LIMIT 10""")
    risk = _all("""SELECT risk_category, COUNT(*) AS total
                   FROM disease_predictions GROUP BY risk_category ORDER BY total DESC""")
    return render_template("admin/dashboard.html", stats=stats, recent_users=recent_users,
                           recent_activity=recent_activity, risk=risk)


@admin_bp.route("/users")
@admin_required
def users():
    q = request.args.get("q", "").strip()
    role = request.args.get("role", "").strip()
    sql = """SELECT id, full_name, email, username, date_of_birth, gender, phone,
                    country, state, city, address, postal_code, role,
                    created_at, updated_at
             FROM users WHERE 1=1"""
    params = []
    if q:
        sql += " AND (full_name LIKE %s OR username LIKE %s OR email LIKE %s OR phone LIKE %s)"
        params += [f"%{q}%"] * 4
    if role:
        sql += " AND role = %s"
        params.append(role)
    sql += " ORDER BY created_at DESC"
    return render_template("admin/users.html", users=_all(sql, params), q=q, role=role)


@admin_bp.route("/users/<int:user_id>", methods=["GET", "POST"])
@admin_required
def user_detail(user_id):
    user = _one("SELECT * FROM users WHERE id = %s", (user_id,))
    if not user:
        abort(404)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            role = request.form.get("role", "researcher").strip()
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE users SET role=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                            (role, user_id))
                cur.close()
            _log("Updated user", "user", user_id, f"role={role}")
            flash("User account updated.", "success")
            return redirect(url_for("admin.user_detail", user_id=user_id))
        if action == "delete":
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                cur.close()
            _log("Deleted user", "user", user_id, "User and linked records deleted by administrator")
            flash("User and linked records were deleted.", "success")
            return redirect(url_for("admin.users"))

    counts = {
        "sequences": _one("SELECT COUNT(*) AS c FROM dna_sequences WHERE user_id=%s", (user_id,))["c"],
        "analyses": _one("""SELECT
            (SELECT COUNT(*) FROM sequence_analysis WHERE user_id=%s) +
            (SELECT COUNT(*) FROM similarity_analysis WHERE user_id=%s) +
            (SELECT COUNT(*) FROM mutation_analyses WHERE user_id=%s) +
            (SELECT COUNT(*) FROM classification_results WHERE user_id=%s) +
            (SELECT COUNT(*) FROM disease_predictions WHERE user_id=%s) AS c""",
                        (user_id,)*5)["c"],
        "reports": _one("SELECT COUNT(*) AS c FROM reports WHERE user_id=%s", (user_id,))["c"],
    }
    return render_template("admin/user_detail.html", user=user, counts=counts)


@admin_bp.route("/dna-uploads")
@admin_required
def dna_uploads():
    q = request.args.get("q", "").strip()
    sql = """SELECT ds.*, u.full_name, u.username, u.email
             FROM dna_sequences ds JOIN users u ON u.id=ds.user_id"""
    params=[]
    if q:
        sql += " WHERE ds.sequence_name LIKE %s OR u.username LIKE %s OR u.email LIKE %s"
        params=[f"%{q}%"]*3
    sql += " ORDER BY ds.created_at DESC"
    rows=_all(sql,params)
    return render_template("admin/dna_uploads.html", rows=rows, q=q)


@admin_bp.route("/predictions")
@admin_required
def predictions():
    rows = _all("""SELECT dp.id, dp.sequence_name, dp.predicted_category, dp.probability,
                          dp.risk_category, dp.model_name, dp.created_at,
                          u.full_name, u.username, u.email
                   FROM disease_predictions dp JOIN users u ON u.id=dp.user_id
                   ORDER BY dp.created_at DESC""")
    classifications = _all("""SELECT cr.id, cr.sequence_name, cr.predicted_class,
                                      cr.confidence, cr.model_name, cr.created_at,
                                      u.full_name, u.username
                               FROM classification_results cr JOIN users u ON u.id=cr.user_id
                               ORDER BY cr.created_at DESC""")
    return render_template("admin/predictions.html", rows=rows, classifications=classifications)


@admin_bp.route("/high-risk")
@admin_required
def high_risk():
    rows = _all("""SELECT dp.*, u.full_name, u.username, u.email, u.phone, u.state, u.city
                   FROM disease_predictions dp JOIN users u ON u.id=dp.user_id
                   WHERE LOWER(dp.risk_category) IN ('high','elevated')
                   ORDER BY dp.created_at DESC""")
    return render_template("admin/high_risk.html", rows=rows)


@admin_bp.route("/reports")
@admin_required
def reports():
    rows = _all("""SELECT r.*, u.full_name, u.username, u.email
                   FROM reports r JOIN users u ON u.id=r.user_id
                   ORDER BY r.created_at DESC""")
    return render_template("admin/reports.html", rows=rows)


@admin_bp.route("/activity-logs")
@admin_required
def activity_logs():
    rows = _all("""SELECT l.*, a.username AS admin_username
                   FROM admin_activity_logs l
                   LEFT JOIN admin_users a ON a.id=l.admin_id
                   ORDER BY l.created_at DESC LIMIT 500""")
    return render_template("admin/activity_logs.html", rows=rows)


@admin_bp.route("/analytics")
@admin_required
def analytics():
    daily_users = _all("""SELECT DATE(created_at) AS day, COUNT(*) AS total
              FROM users GROUP BY DATE(created_at)
                          ORDER BY day DESC LIMIT 30""")
    daily_sequences = _all("""SELECT DATE(created_at) AS day, COUNT(*) AS total
                  FROM dna_sequences GROUP BY DATE(created_at)
                              ORDER BY day DESC LIMIT 30""")
    risk = _all("""SELECT risk_category, COUNT(*) AS total
                   FROM disease_predictions GROUP BY risk_category""")
    modules = _all("""SELECT 'DNA Uploads' AS module, COUNT(*) AS total FROM dna_sequences
                      UNION ALL SELECT 'Sequence Analysis', COUNT(*) FROM sequence_analysis
                      UNION ALL SELECT 'Similarity Analysis', COUNT(*) FROM similarity_analysis
                      UNION ALL SELECT 'Mutation Analysis', COUNT(*) FROM mutation_analyses
                      UNION ALL SELECT 'Classification', COUNT(*) FROM classification_results
                      UNION ALL SELECT 'Disease Prediction', COUNT(*) FROM disease_predictions
                      UNION ALL SELECT 'Complete Analysis', COUNT(*) FROM complete_analyses""")
    return render_template("admin/analytics.html", daily_users=list(reversed(daily_users)),
                           daily_sequences=list(reversed(daily_sequences)), risk=risk, modules=modules)


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "theme":
            theme = request.form.get("theme", "dark")
            if theme not in {"dark", "light", "system"}:
                theme = "dark"
            with get_db() as conn:
                cur=conn.cursor()
                cur.execute("""INSERT INTO admin_settings(setting_key,setting_value)
                               VALUES (%s,%s)
                               ON DUPLICATE KEY UPDATE
                               setting_value=VALUES(setting_value), updated_at=CURRENT_TIMESTAMP""",
                            ("theme", theme))
                cur.close()
            _log("Changed admin theme", "settings", None, theme)
            flash("Admin theme preference saved.", "success")
        elif action == "password":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            admin = _one("SELECT * FROM admin_users WHERE id=%s", (session["admin_id"],))
            if not admin or not check_password_hash(admin["password_hash"], current):
                flash("Current admin password is incorrect.", "danger")
            elif len(new) < 8:
                flash("New password must contain at least 8 characters.", "danger")
            elif new != confirm:
                flash("New passwords do not match.", "danger")
            else:
                with get_db() as conn:
                    cur=conn.cursor()
                    cur.execute("UPDATE admin_users SET password_hash=%s WHERE id=%s",
                                (generate_password_hash(new), session["admin_id"]))
                    cur.close()
                _log("Changed admin password", "admin", session["admin_id"], "Password updated")
                flash("Administrator password changed successfully.", "success")

    row=_one("SELECT setting_value FROM admin_settings WHERE setting_key='theme'")
    theme=row["setting_value"] if row else "dark"
    return render_template("admin/settings.html", theme=theme)
