import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from ml.disease.train import train_disease_random_forest

if __name__ == "__main__":
    train_disease_random_forest()
