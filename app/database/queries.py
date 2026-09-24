import json
import logging
from typing import List, Dict, Any, Optional
from app.database.connection import get_db

logger = logging.getLogger(__name__)


# ============================================================================
# USER QUERIES
# ============================================================================

def create_user(
    full_name: str,
    email: str,
    username: str,
    password_hash: str,
    role: str = 'researcher',
    date_of_birth: Optional[str] = None,
    gender: Optional[str] = None,
    phone: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    address: Optional[str] = None,
    postal_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    blood_group: Optional[str] = None,
    height: Optional[float] = None,
    weight: Optional[float] = None
) -> int:
    query = """
        INSERT INTO users (full_name, email, username, password_hash, role, date_of_birth, gender, phone, country, state, city, address, postal_code, latitude, longitude, blood_group, height, weight)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    dob_val = date_of_birth if date_of_birth and date_of_birth.strip() else None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            full_name.strip(),
            email.strip().lower(),
            username.strip().lower(),
            password_hash,
            role,
            dob_val,
            gender.strip() if gender else None,
            phone.strip() if phone else None,
            country.strip() if country else None,
            state.strip() if state else None,
            city.strip() if city else None,
            address.strip() if address else None,
            postal_code.strip() if postal_code else None,
            latitude,
            longitude,
            blood_group.strip() if blood_group else None,
            height,
            weight
        ))
        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return user_id


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT id, full_name, email, username, password_hash, role, date_of_birth, gender, phone, country, state, city, address, postal_code, latitude, longitude, blood_group, height, weight, created_at FROM users WHERE id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    query = """
        SELECT id, full_name, email, username, password_hash, role, date_of_birth, gender, phone, country, state, city, address, postal_code, blood_group, height, weight, created_at 
        FROM users 
        WHERE username = %s OR email = %s
    """
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (identifier.lower(), identifier.lower()))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    query = "SELECT id, full_name, email, username, password_hash, role, date_of_birth, gender, phone, country, state, city, address, postal_code, blood_group, height, weight, created_at FROM users WHERE username = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (username.lower(),))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    query = "SELECT id, full_name, email, username, password_hash, role, date_of_birth, gender, phone, country, state, city, address, postal_code, blood_group, height, weight, created_at FROM users WHERE email = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (email.lower(),))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def update_user_profile(user_id: int, full_name: str, email: str, phone: Optional[str] = None, address: Optional[str] = None, city: Optional[str] = None, state: Optional[str] = None, country: Optional[str] = None, postal_code: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, blood_group: Optional[str] = None, height: Optional[float] = None, weight: Optional[float] = None) -> bool:
    query = "UPDATE users SET full_name = %s, email = %s, phone = %s, address = %s, city = %s, state = %s, country = %s, postal_code = %s, latitude = %s, longitude = %s, blood_group = %s, height = %s, weight = %s WHERE id = %s"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (full_name, email.lower(), phone, address, city, state, country, postal_code, latitude, longitude, blood_group, height, weight, user_id))
        affected = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return affected


def update_user_password(user_id: int, password_hash: str) -> bool:
    query = "UPDATE users SET password_hash = %s WHERE id = %s"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (password_hash, user_id))
        affected = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return affected


# ============================================================================
# DNA SEQUENCE QUERIES
# ============================================================================

def create_dna_sequence(user_id: int, sequence_name: str, sequence: str, sequence_length: int,
                        source_type: str = 'manual', description: str = '') -> int:
    query = """
        INSERT INTO dna_sequences (user_id, sequence_name, sequence, sequence_length, source_type, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id, sequence_name, sequence, sequence_length, source_type, description))
        seq_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return seq_id


def get_dna_sequence_by_id(sequence_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM dna_sequences WHERE id = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (sequence_id, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_user_dna_sequences(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    query = "SELECT id, sequence_name, sequence_length, source_type, created_at FROM dna_sequences WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (user_id, limit))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
        return results


# ============================================================================
# MODULE 1: SEQUENCE ANALYSIS QUERIES
# ============================================================================

def save_sequence_analysis(user_id: int, sequence_id: Optional[int], sequence_name: str,
                           length: int, a_count: int, t_count: int, g_count: int, c_count: int,
                           a_percentage: float, t_percentage: float, g_percentage: float, c_percentage: float,
                           gc_content: float, at_content: float, purine_count: int, pyrimidine_count: int,
                           molecular_weight: float) -> int:
    query = """
        INSERT INTO sequence_analysis (
            user_id, sequence_id, sequence_name, length, a_count, t_count, g_count, c_count,
            a_percentage, t_percentage, g_percentage, c_percentage, gc_content, at_content,
            purine_count, pyrimidine_count, molecular_weight
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            user_id, sequence_id, sequence_name, length, a_count, t_count, g_count, c_count,
            a_percentage, t_percentage, g_percentage, c_percentage, gc_content, at_content,
            purine_count, pyrimidine_count, molecular_weight
        ))
        analysis_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return analysis_id


def get_sequence_analysis_by_id(analysis_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = """
        SELECT sa.*, ds.sequence 
        FROM sequence_analysis sa
        LEFT JOIN dna_sequences ds ON sa.sequence_id = ds.id
        WHERE sa.id = %s AND sa.user_id = %s
    """
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (analysis_id, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_user_sequence_analyses(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    query = "SELECT * FROM sequence_analysis WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (user_id, limit))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
        return results


# ============================================================================
# MODULE 2: SIMILARITY ANALYSIS QUERIES
# ============================================================================

def save_similarity_analysis(user_id: int, ref_id: Optional[int], query_id: Optional[int],
                            ref_name: str, query_name: str, ref_len: int, query_len: int,
                            sim_pct: float, diff_pct: float, matches: int, mismatches: int,
                            gaps: int, score: float, align_ref: str, align_query: str, align_match: str) -> int:
    query = """
        INSERT INTO similarity_analysis (
            user_id, reference_sequence_id, query_sequence_id, reference_name, query_name,
            reference_length, query_length, similarity_percentage, difference_percentage,
            match_count, mismatch_count, gap_count, alignment_score, alignment_ref,
            alignment_query, alignment_match
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            user_id, ref_id, query_id, ref_name, query_name, ref_len, query_len,
            sim_pct, diff_pct, matches, mismatches, gaps, score, align_ref, align_query, align_match
        ))
        analysis_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return analysis_id


def get_similarity_analysis_by_id(analysis_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM similarity_analysis WHERE id = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (analysis_id, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


# ============================================================================
# MODULE 3: MUTATION ANALYSIS QUERIES
# ============================================================================

def save_mutation_analysis(user_id: int, ref_id: Optional[int], sample_id: Optional[int],
                           ref_name: str, sample_name: str, total_mut: int, subs: int,
                           ins: int, dels: int, mutation_rate: float) -> int:
    query = """
        INSERT INTO mutation_analyses (
            user_id, reference_sequence_id, sample_sequence_id, reference_name, sample_name,
            total_mutations, substitutions_count, insertions_count, deletions_count, mutation_rate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id, ref_id, sample_id, ref_name, sample_name, total_mut, subs, ins, dels, mutation_rate))
        analysis_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return analysis_id


def save_mutations_batch(user_id: int, analysis_id: int, mutations_list: List[Dict[str, Any]]):
    if not mutations_list:
        return
    query = """
        INSERT INTO mutations (user_id, analysis_id, position, mutation_type, reference_base, observed_base, consequence_note)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    data = [
        (user_id, analysis_id, m['position'], m['type'], m['ref_base'], m['obs_base'], m.get('note', ''))
        for m in mutations_list
    ]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.executemany(query, data)
        cursor.close()


def get_mutation_analysis_by_id(analysis_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM mutation_analyses WHERE id = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (analysis_id, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_mutations_by_analysis_id(analysis_id: int, user_id: int) -> List[Dict[str, Any]]:
    query = "SELECT * FROM mutations WHERE analysis_id = %s AND user_id = %s ORDER BY position ASC"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (analysis_id, user_id))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
        return results


# ============================================================================
# MODULE 4: CLASSIFICATION QUERIES
# ============================================================================

def save_classification_result(user_id: int, sequence_id: Optional[int], sequence_name: str,
                               model_name: str, predicted_class: str, confidence: float,
                               features: Dict[str, Any], probabilities: Dict[str, float]) -> int:
    query = """
        INSERT INTO classification_results (
            user_id, sequence_id, sequence_name, model_name, predicted_class, confidence,
            features_json, probabilities_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            user_id, sequence_id, sequence_name, model_name, predicted_class, confidence,
            json.dumps(features), json.dumps(probabilities)
        ))
        res_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return res_id


def get_classification_by_id(result_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM classification_results WHERE id = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (result_id, user_id))
        result = cursor.fetchone()
        if result and result.get('features_json'):
            result['features'] = json.loads(result['features_json'])
        if result and result.get('probabilities_json'):
            result['probabilities'] = json.loads(result['probabilities_json'])
        conn.commit()
        cursor.close()
        return result


# ============================================================================
# MODULE 5: DISEASE PREDICTION QUERIES
# ============================================================================

def save_disease_prediction(user_id: int, sequence_id: Optional[int], sequence_name: str,
                            model_name: str, predicted_category: str, probability: float,
                            risk_category: str, features: Dict[str, Any], disclaimer: str,
                            probabilities: Optional[Dict[str, float]] = None) -> int:
    query = """
        INSERT INTO disease_predictions (
            user_id, sequence_id, sequence_name, model_name, predicted_category, probability,
            risk_category, features_json, probabilities_json, disclaimer_notice
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            user_id, sequence_id, sequence_name, model_name, predicted_category, float(probability),
            risk_category, json.dumps(features), json.dumps(probabilities) if probabilities else None, disclaimer
        ))
        res_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return res_id


def get_disease_prediction_by_id(pred_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = """
        SELECT dp.*, ds.sequence
        FROM disease_predictions dp
        LEFT JOIN dna_sequences ds ON dp.sequence_id = ds.id
        WHERE dp.id = %s AND dp.user_id = %s
    """
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (pred_id, user_id))
        result = cursor.fetchone()
        if result and result.get('features_json'):
            result['features'] = json.loads(result['features_json'])
        if result and result.get('probabilities_json'):
            result['probabilities'] = json.loads(result['probabilities_json'])
        conn.commit()
        cursor.close()
        return result


# ============================================================================
# MODULE 6: VISUALIZATIONS QUERIES
# ============================================================================

def save_visualization(user_id: int, sequence_id: Optional[int], sequence_name: str,
                       visualization_type: str, chart_config: Dict[str, Any]) -> int:
    query = """
        INSERT INTO visualizations (user_id, sequence_id, sequence_name, visualization_type, chart_config_json)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id, sequence_id, sequence_name, visualization_type, json.dumps(chart_config)))
        vis_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return vis_id


def get_visualization_by_id(vis_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM visualizations WHERE id = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (vis_id, user_id))
        result = cursor.fetchone()
        if result and result.get('chart_config_json'):
            result['chart_config'] = json.loads(result['chart_config_json'])
        conn.commit()
        cursor.close()
        return result


# ============================================================================
# COMPLETE DNA ANALYSES QUERIES
# ============================================================================

def create_complete_analysis(user_id: int, sequence_id: Optional[int], ref_id: Optional[int],
                             sequence_name: str, sa_id: int, sim_id: int, mut_id: int,
                             clf_id: int, dis_id: int, summary: Dict[str, Any]) -> int:
    query = """
        INSERT INTO complete_analyses (
            user_id, sequence_id, reference_sequence_id, sequence_name, status,
            sequence_analysis_id, similarity_analysis_id, mutation_analysis_id,
            classification_id, disease_prediction_id, summary_metrics_json
        ) VALUES (%s, %s, %s, %s, 'COMPLETED', %s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            user_id, sequence_id, ref_id, sequence_name,
            sa_id, sim_id, mut_id, clf_id, dis_id, json.dumps(summary)
        ))
        comp_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return comp_id


def get_complete_analysis_by_id(comp_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = """
        SELECT ca.*,
               sa.length, sa.gc_content, sa.at_content, sa.a_percentage, sa.t_percentage, sa.g_percentage, sa.c_percentage,
               sa.a_count, sa.t_count, sa.g_count, sa.c_count, sa.molecular_weight,
               sim.similarity_percentage, sim.difference_percentage, sim.match_count, sim.mismatch_count, sim.gap_count,
               sim.reference_name, sim.query_name, sim.alignment_ref, sim.alignment_query, sim.alignment_match,
               ma.total_mutations, ma.substitutions_count, ma.insertions_count, ma.deletions_count, ma.mutation_rate,
               cr.predicted_class, cr.confidence as class_confidence, cr.probabilities_json,
               dp.predicted_category, dp.probability as disease_probability, dp.risk_category, dp.disclaimer_notice,
               ds.sequence,
               ds_ref.sequence as reference_sequence
        FROM complete_analyses ca
        LEFT JOIN sequence_analysis sa ON ca.sequence_analysis_id = sa.id
        LEFT JOIN similarity_analysis sim ON ca.similarity_analysis_id = sim.id
        LEFT JOIN mutation_analyses ma ON ca.mutation_analysis_id = ma.id
        LEFT JOIN classification_results cr ON ca.classification_id = cr.id
        LEFT JOIN disease_predictions dp ON ca.disease_prediction_id = dp.id
        LEFT JOIN dna_sequences ds ON ca.sequence_id = ds.id
        LEFT JOIN dna_sequences ds_ref ON sim.reference_sequence_id = ds_ref.id
        WHERE ca.id = %s AND ca.user_id = %s
    """
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (comp_id, user_id))
        result = cursor.fetchone()
        if result and result.get('summary_metrics_json'):
            result['summary_metrics'] = json.loads(result['summary_metrics_json'])
        if result and result.get('probabilities_json'):
            result['probabilities'] = json.loads(result['probabilities_json'])
        conn.commit()
        cursor.close()
        return result


# ============================================================================
# REPORTS QUERIES
# ============================================================================

def create_report_record(user_id: int, report_uuid: str, analysis_id: Optional[int],
                         analysis_type: str, title: str, file_name: str, file_path: str,
                         file_size_bytes: int) -> int:
    query = """
        INSERT INTO reports (user_id, report_uuid, analysis_id, analysis_type, title, file_name, file_path, file_size_bytes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id, report_uuid, analysis_id, analysis_type, title, file_name, file_path, file_size_bytes))
        report_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return report_id


def get_report_by_uuid(report_uuid: str, user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM reports WHERE report_uuid = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (report_uuid, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_report_by_id(report_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM reports WHERE id = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (report_id, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result


def get_user_reports(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    query = "SELECT * FROM reports WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (user_id, limit))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
        return results


def delete_report(report_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    report = get_report_by_id(report_id, user_id)
    if report:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reports WHERE id = %s AND user_id = %s", (report_id, user_id))
            conn.commit()
        cursor.close()
    return report


# ============================================================================
# DASHBOARD STATS & COMBINED HISTORY
# ============================================================================

def get_user_dashboard_stats(user_id: int) -> Dict[str, Any]:
    stats = {
        "total_analyses": 0,
        "total_sequences": 0,
        "total_mutations_detected": 0,
        "total_classifications": 0,
        "total_disease_predictions": 0,
        "total_reports": 0,
        "total_complete_analyses": 0,
        "recent_activities": []
    }
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as c FROM dna_sequences WHERE user_id = %s", (user_id,))
        stats["total_sequences"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM sequence_analysis WHERE user_id = %s", (user_id,))
        seq_count = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_mutations), 0) as m FROM mutation_analyses WHERE user_id = %s", (user_id,))
        mut_res = cursor.fetchone()
        mut_count = mut_res["c"]
        stats["total_mutations_detected"] = int(mut_res["m"])

        cursor.execute("SELECT COUNT(*) as c FROM similarity_analysis WHERE user_id = %s", (user_id,))
        sim_count = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM classification_results WHERE user_id = %s", (user_id,))
        stats["total_classifications"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM disease_predictions WHERE user_id = %s", (user_id,))
        stats["total_disease_predictions"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM reports WHERE user_id = %s", (user_id,))
        stats["total_reports"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM complete_analyses WHERE user_id = %s", (user_id,))
        stats["total_complete_analyses"] = cursor.fetchone()["c"]

        stats["total_analyses"] = (
            seq_count + sim_count + mut_count +
            stats["total_classifications"] + stats["total_disease_predictions"] +
            stats["total_complete_analyses"]
        )

        # Recent complete and individual analyses
        cursor.execute("""
            SELECT id, 'complete' as type, sequence_name as title, status, created_at, NULL as outcome
            FROM complete_analyses WHERE user_id = %s
            UNION ALL
            SELECT id, 'sequence' as type, sequence_name as title, 'COMPLETED' as status, created_at, CONCAT('GC: ', gc_content, '%%') as outcome
            FROM sequence_analysis WHERE user_id = %s
            UNION ALL
            SELECT id, 'classification' as type, sequence_name as title, 'COMPLETED' as status, created_at, CONCAT(predicted_class, ' (', confidence, '%%)') as outcome
            FROM classification_results WHERE user_id = %s
            UNION ALL
            SELECT id, 'disease' as type, sequence_name as title, 'COMPLETED' as status, created_at, CONCAT(predicted_category, ' [', risk_category, ']') as outcome
            FROM disease_predictions WHERE user_id = %s
            ORDER BY created_at DESC LIMIT 6
        """, (user_id, user_id, user_id, user_id))
        stats["recent_activities"] = cursor.fetchall()

        conn.commit()
        cursor.close()
        return stats


def get_user_combined_history(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    query = """
        SELECT 
            ca.id as id,
            'Complete DNA Analysis' as module_name,
            'complete' as module_type,
            ca.sequence_name,
            ca.sequence_id,
            cr.predicted_class as classification_result,
            dp.predicted_category as disease_prediction,
            dp.risk_category,
            ca.status,
            ca.created_at,
            ca.id as detail_id
        FROM complete_analyses ca
        LEFT JOIN classification_results cr ON ca.classification_id = cr.id
        LEFT JOIN disease_predictions dp ON ca.disease_prediction_id = dp.id
        WHERE ca.user_id = %s

        UNION ALL

        SELECT 
            sa.id as id,
            'Sequence Processing & Analysis' as module_name,
            'sequence' as module_type,
            sa.sequence_name,
            sa.sequence_id,
            CONCAT('GC: ', sa.gc_content, '%%') as classification_result,
            CONCAT('Length: ', sa.length, ' bp') as disease_prediction,
            'N/A' as risk_category,
            'COMPLETED' as status,
            sa.created_at,
            sa.id as detail_id
        FROM sequence_analysis sa
        WHERE sa.user_id = %s

        UNION ALL

        SELECT 
            sim.id as id,
            'DNA Similarity Analysis' as module_name,
            'similarity' as module_type,
            CONCAT(sim.reference_name, ' vs ', sim.query_name) as sequence_name,
            sim.query_sequence_id as sequence_id,
            CONCAT('Similarity: ', sim.similarity_percentage, '%%') as classification_result,
            CONCAT('Matches: ', sim.match_count, ' / ', (sim.match_count + sim.mismatch_count + sim.gap_count)) as disease_prediction,
            'N/A' as risk_category,
            'COMPLETED' as status,
            sim.created_at,
            sim.id as detail_id
        FROM similarity_analysis sim
        WHERE sim.user_id = %s

        UNION ALL

        SELECT 
            ma.id as id,
            'Mutation Detection & Analysis' as module_name,
            'mutation' as module_type,
            CONCAT(ma.reference_name, ' vs ', ma.sample_name) as sequence_name,
            ma.sample_sequence_id as sequence_id,
            CONCAT('Total Mut: ', ma.total_mutations) as classification_result,
            CONCAT('Sub: ', ma.substitutions_count, ', Ins: ', ma.insertions_count, ', Del: ', ma.deletions_count) as disease_prediction,
            'N/A' as risk_category,
            'COMPLETED' as status,
            ma.created_at,
            ma.id as detail_id
        FROM mutation_analyses ma
        WHERE ma.user_id = %s

        UNION ALL

        SELECT 
            cr.id as id,
            'AI-Based DNA Classification' as module_name,
            'classification' as module_type,
            cr.sequence_name,
            cr.sequence_id,
            cr.predicted_class as classification_result,
            CONCAT('Confidence: ', cr.confidence, '%%') as disease_prediction,
            'N/A' as risk_category,
            'COMPLETED' as status,
            cr.created_at,
            cr.id as detail_id
        FROM classification_results cr
        WHERE cr.user_id = %s

        UNION ALL

        SELECT 
            dp.id as id,
            'Disease Risk Prediction' as module_name,
            'disease' as module_type,
            dp.sequence_name,
            dp.sequence_id,
            dp.predicted_category as classification_result,
            CONCAT('Prob: ', dp.probability, '%%') as disease_prediction,
            dp.risk_category,
            'COMPLETED' as status,
            dp.created_at,
            dp.id as detail_id
        FROM disease_predictions dp
        WHERE dp.user_id = %s

        ORDER BY created_at DESC
        LIMIT %s
    """
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (user_id, user_id, user_id, user_id, user_id, user_id, limit))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
        return results
