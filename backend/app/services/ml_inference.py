from typing import Any, Dict
import joblib
import numpy as np

class MLInference:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

    def predict(self, features: np.ndarray) -> Any:
        """
        Make a prediction using the loaded machine learning model.

        :param features: A numpy array of features for prediction.
        :return: The prediction result.
        """
        return self.model.predict(features)

    def prepare_features(self, user_data: Dict[str, Any]) -> np.ndarray:
        """
        Prepare features for the model based on user data.

        :param user_data: A dictionary containing user data.
        :return: A numpy array of features.
        """
        # Example feature preparation logic
        # This should be customized based on the actual features used in the model
        features = np.array([
            user_data.get('body_type', 0),
            user_data.get('weather_condition', 0),
            user_data.get('wardrobe_items_count', 0),
            # Add more features as needed
        ])
        return features

# Example usage:
# ml_inference = MLInference(model_path='path/to/saved_model.pkl')
# user_data = {'body_type': 1, 'weather_condition': 2, 'wardrobe_items_count': 5}
# features = ml_inference.prepare_features(user_data)
# prediction = ml_inference.predict(features)