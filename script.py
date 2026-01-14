from joblib import Memory
import pickle

import joblib


loaded_model = joblib.load('models/model.pkl')
joblib.dump(loaded_model, 'models/model_joblib')
