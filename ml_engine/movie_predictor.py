import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.metrics import r2_score, mean_absolute_error, accuracy_score
from database.db_connection import get_db_connection

class MovieAutoMLEngine:
    """
    Automated Machine Learning & Predictive Analytics Engine for VoiceSQL Studio.
    Performs on-the-fly model training:
    1. Box Office Revenue Regression (Linear Regression & Random Forest)
    2. Commercial Success Classification (Blockbuster / Moderate Hit / Flop)
    3. Unsupervised Anomaly & Outlier Detection (Isolation Forest)
    """

    def __init__(self):
        self.df = None
        self.reg_rf = None
        self.clf_rf = None
        self.iso_forest = None
        self.feature_columns = None
        self.metrics = {}
        self._is_trained = False

    def load_data(self) -> pd.DataFrame:
        """Fetch movie data from database."""
        conn = get_db_connection()
        query = """
        SELECT m.movie_id, m.title, m.release_year, m.genre, m.rating, 
               m.votes, m.duration_min, m.budget_millions, m.box_office_millions, 
               m.streaming_platform, d.director_name, d.oscars_won
        FROM movies m
        LEFT JOIN directors d ON m.director_id = d.director_id
        WHERE m.budget_millions IS NOT NULL AND m.box_office_millions IS NOT NULL;
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Calculate Return on Investment (ROI)
        df["roi_multiple"] = df["box_office_millions"] / np.maximum(df["budget_millions"], 0.01)
        df["profit_millions"] = df["box_office_millions"] - df["budget_millions"]

        # Define Commercial Success Class
        def label_success(row):
            if row["roi_multiple"] >= 2.5 and row["rating"] >= 7.0:
                return "Blockbuster Hit"
            elif row["roi_multiple"] >= 1.2:
                return "Moderate Hit"
            else:
                return "Box Office Flop"

        df["commercial_verdict"] = df.apply(label_success, axis=1)
        self.df = df
        return df

    def train_models(self):
        """Train regression, classification, and anomaly models on the dataset."""
        if self.df is None or len(self.df) < 10:
            self.load_data()

        df = self.df.copy()

        # Feature preprocessing: one-hot encode Genre
        df_encoded = pd.get_dummies(df, columns=["genre"], drop_first=False)
        genre_cols = [c for c in df_encoded.columns if c.startswith("genre_")]
        
        base_features = ["budget_millions", "rating", "duration_min", "release_year", "oscars_won"]
        self.feature_columns = base_features + genre_cols

        X = df_encoded[self.feature_columns].fillna(0)
        y_reg = df_encoded["box_office_millions"]
        y_clf = df_encoded["commercial_verdict"]

        X_train, X_test, y_reg_train, y_reg_test = train_test_split(X, y_reg, test_size=0.20, random_state=42)
        _, _, y_clf_train, y_clf_test = train_test_split(X, y_clf, test_size=0.20, random_state=42)

        # 1. Regression: Random Forest Regressor
        self.reg_rf = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
        self.reg_rf.fit(X_train, y_reg_train)
        y_reg_pred = self.reg_rf.predict(X_test)
        
        r2 = r2_score(y_reg_test, y_reg_pred)
        mae = mean_absolute_error(y_reg_test, y_reg_pred)

        # Baseline Linear Regression for comparison
        lin_reg = LinearRegression()
        lin_reg.fit(X_train, y_reg_train)
        lin_r2 = r2_score(y_reg_test, lin_reg.predict(X_test))

        # 2. Classification: Random Forest Classifier
        self.clf_rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        self.clf_rf.fit(X_train, y_clf_train)
        y_clf_pred = self.clf_rf.predict(X_test)
        accuracy = accuracy_score(y_clf_test, y_clf_pred)

        # 3. Anomaly Detection: Isolation Forest
        anomaly_feats = df[["budget_millions", "box_office_millions", "rating", "roi_multiple"]].fillna(0)
        self.iso_forest = IsolationForest(contamination=0.08, random_state=42)
        df["anomaly_score"] = self.iso_forest.fit_predict(anomaly_feats)
        df["is_anomaly"] = df["anomaly_score"] == -1
        self.df = df

        self.metrics = {
            "r2_score": max(0.0, round(float(r2), 3)),
            "linear_r2": max(0.0, round(float(lin_r2), 3)),
            "mae_millions": round(float(mae), 1),
            "clf_accuracy": round(float(accuracy * 100), 1),
            "total_samples": len(df),
            "features_used": len(self.feature_columns)
        }
        self._is_trained = True
        return self.metrics

    def predict_new_movie(self, budget_millions: float, genre: str, rating: float = 7.5, 
                          duration_min: int = 120, release_year: int = 2025, oscars_won: int = 0) -> dict:
        """Runs real-time inference on user-configured production parameters."""
        if not self._is_trained:
            self.train_models()

        input_dict = {
            "budget_millions": budget_millions,
            "rating": rating,
            "duration_min": duration_min,
            "release_year": release_year,
            "oscars_won": oscars_won
        }
        for col in self.feature_columns:
            if col.startswith("genre_"):
                target_g = col.replace("genre_", "")
                input_dict[col] = 1 if genre.lower() == target_g.lower() else 0

        input_df = pd.DataFrame([input_dict])[self.feature_columns]

        # 1. Regress Box Office
        pred_gross = float(self.reg_rf.predict(input_df)[0])
        pred_gross = max(0.5, round(pred_gross, 1))

        # 2. Classify Commercial Success
        pred_class = str(self.clf_rf.predict(input_df)[0])
        class_probs = self.clf_rf.predict_proba(input_df)[0]
        classes = self.clf_rf.classes_
        prob_dict = {classes[i]: round(float(class_probs[i] * 100), 1) for i in range(len(classes))}

        # 3. Calculate ROI & Profit
        pred_roi = round(pred_gross / max(budget_millions, 0.01), 2)
        pred_profit = round(pred_gross - budget_millions, 1)

        return {
            "predicted_box_office": pred_gross,
            "predicted_roi": pred_roi,
            "predicted_profit": pred_profit,
            "success_verdict": pred_class,
            "class_probabilities": prob_dict
        }

    def get_detected_anomalies(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Separate anomalies into High-ROI Super-Performers and Massive Budget Disasters."""
        if not self._is_trained:
            self.train_models()

        anomalies = self.df[self.df["is_anomaly"]].copy()
        
        # High-ROI Super-Performers: low budget (< 25M) with huge box office
        super_performers = anomalies[anomalies["roi_multiple"] >= 5.0].sort_values(by="roi_multiple", ascending=False)
        
        # Disasters: high budget (> 70M) with low ROI (< 1.5x)
        box_office_disasters = anomalies[(anomalies["budget_millions"] >= 70.0) & (anomalies["roi_multiple"] < 1.4)].sort_values(by="budget_millions", ascending=False)

        return super_performers, box_office_disasters

# Singleton instance
movie_automl = MovieAutoMLEngine()
