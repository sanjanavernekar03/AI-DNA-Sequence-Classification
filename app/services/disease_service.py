from typing import Dict, Any, Optional
from app.ml.predict_disease import predict_disease_risk
from app.database.queries import save_disease_prediction, get_disease_prediction_by_id


def process_disease_prediction(user_id: int, sequence: str, sequence_name: str = "DNA Sequence",
                               sequence_id: Optional[int] = None) -> Dict[str, Any]:
    """Execute AI disease/genomic risk prediction and store result in database."""
    res = predict_disease_risk(sequence)

    db_id = save_disease_prediction(
        user_id=user_id,
        sequence_id=sequence_id,
        sequence_name=sequence_name,
        model_name=res["model_name"],
        predicted_category=res["predicted_category"],
        probability=res["probability"],
        risk_category=res["risk_category"],
        features=res["extracted_features_sample"],
        disclaimer=res["disclaimer_notice"],
        probabilities=res.get("probabilities")
    )

    res["id"] = db_id
    res["sequence_name"] = sequence_name
    return res
