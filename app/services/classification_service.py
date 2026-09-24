from typing import Dict, Any, Optional
from app.ml.predict_classification import predict_dna_class
from app.database.queries import save_classification_result, get_classification_by_id


def process_dna_classification(user_id: int, sequence: str, sequence_name: str = "DNA Sequence",
                               sequence_id: Optional[int] = None) -> Dict[str, Any]:
    """Execute AI classification on DNA sequence and record result in database."""
    res = predict_dna_class(sequence)

    db_id = save_classification_result(
        user_id=user_id,
        sequence_id=sequence_id,
        sequence_name=sequence_name,
        model_name=res["model_name"],
        predicted_class=res["predicted_class"],
        confidence=res["confidence"],
        features=res["extracted_features_sample"],
        probabilities=res["probabilities"]
    )

    res["id"] = db_id
    res["sequence_name"] = sequence_name
    return res
