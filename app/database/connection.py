import mysql.connector
from mysql.connector import pooling, Error
import logging
from contextlib import contextmanager
from app.config import Config

logger = logging.getLogger(__name__)

db_pool = None

def init_connection_pool():
    global db_pool
    if db_pool is None:
        try:
            # First, attempt to create the database if it does not exist
            _create_database_if_not_exists()
            
            db_pool = pooling.MySQLConnectionPool(
                pool_name="dna_app_pool",
                pool_size=5,
                pool_reset_session=True,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                auth_plugin='mysql_native_password'
            )
            logger.info(f"MySQL Connection Pool established for {Config.DB_NAME}")
            
            _init_database_schema()
        except Error as e:
            logger.error(f"Failed to initialize MySQL connection pool: {e}")
            raise

def _create_database_if_not_exists():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            auth_plugin='mysql_native_password'
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
            cursor.close()
            conn.close()
    except Error as e:
        logger.error(f"Failed to create database: {e}")
        raise

def _init_database_schema():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if users table exists. If not, we run the schema script.
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            logger.info("Initializing database schema from schema.sql...")
            import os
            schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # Split and execute each statement
                statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                for statement in statements:
                    try:
                        cursor.execute(statement)
                    except Error as e:
                        logger.error(f"Error executing schema statement: {e}\nStatement: {statement[:100]}...")
            conn.commit()

        # Add new health fields if they don't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN blood_group VARCHAR(10) NULL, ADD COLUMN height REAL NULL, ADD COLUMN weight REAL NULL")
            conn.commit()
            logger.info("Successfully added health fields to users table.")
        except Error as e:
            # Code 1060: Duplicate column name
            if e.errno != 1060:
                logger.warning(f"Note on altering users table: {e}")

        # Admin tables may be missing in databases created before the admin module.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(150) NOT NULL DEFAULT 'Admin',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_id INT NULL,
                action VARCHAR(255) NOT NULL,
                target_type VARCHAR(255),
                target_id INT,
                details TEXT,
                ip_address VARCHAR(150),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(150) NOT NULL UNIQUE,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # Bring older MySQL databases up to the columns used by admin screens.
        cursor.execute("""
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users'
        """, (Config.DB_NAME,))
        user_columns = {row[0] for row in cursor.fetchall()}
        if "is_active" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1")
        if "last_login_at" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP NULL")
        if "last_activity_at" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_activity_at TIMESTAMP NULL")
        if "latitude" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN latitude REAL NULL")
        if "longitude" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN longitude REAL NULL")
            
        # Ensure appointments table has new fields
        cursor.execute("SHOW TABLES LIKE 'appointments'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='appointments'
            """, (Config.DB_NAME,))
            appt_columns = {row[0] for row in cursor.fetchall()}
            if "patient_email" not in appt_columns:
                cursor.execute("ALTER TABLE appointments ADD COLUMN patient_email VARCHAR(255) NOT NULL DEFAULT ''")
            if "consultation_fee" not in appt_columns:
                cursor.execute("ALTER TABLE appointments ADD COLUMN consultation_fee DECIMAL(10,2) NULL")

        # Ensure disease_predictions table has probabilities_json column
        cursor.execute("SHOW TABLES LIKE 'disease_predictions'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='disease_predictions'
            """, (Config.DB_NAME,))
            dp_columns = {row[0] for row in cursor.fetchall()}
            if "probabilities_json" not in dp_columns:
                cursor.execute("ALTER TABLE disease_predictions ADD COLUMN probabilities_json TEXT NULL")

        # Create the local admin account only when it does not already exist.
        from werkzeug.security import generate_password_hash
        username = Config.ADMIN_USERNAME.strip() or "admin"
        cursor.execute("SELECT id FROM admin_users WHERE username = %s", (username,))
        if not cursor.fetchone():
            cursor.execute(
                """INSERT INTO admin_users
                   (username, password_hash, display_name, is_active)
                   VALUES (%s, %s, %s, %s)""",
                (username, generate_password_hash(Config.ADMIN_PASSWORD), "System Admin", 1)
            )

        conn.commit()
        cursor.close()

@contextmanager
def get_db():
    global db_pool
    if db_pool is None:
        init_connection_pool()
        
    conn = None
    try:
        conn = db_pool.get_connection()
        conn.autocommit = True
        yield conn
        conn.commit()
    except Error as e:
        logger.error(f"MySQL Error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()
