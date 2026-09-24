from ml.disease.predict import predict_dna_disease, load_disease_model

def predict_disease_risk(sequence):
    return predict_dna_disease(sequence)

def get_disease_model():
    return load_disease_model()
