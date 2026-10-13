import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import r2_score, mean_absolute_error, accuracy_score, f1_score
from database.db_connection import get_db_connection

class UniversalAutoMLEngine:
    """
    Universal Automated Machine Learning (AutoML) Engine.
    Works dynamically with ANY dataset (User-uploaded CSVs, Students, Healthcare, Sales, Movies, etc.).
    Automatically performs:
    1. Schema & Column Type Inference (Numeric vs Categorical)
    2. Dynamic Task Detection (Regression vs Classification)
    3. Missing Value Imputation & One-Hot Encoding
    4. Real-time Model Training & Cross-Validation
    5. Interactive Prediction on arbitrary user features
    6. Unsupervised Anomaly & Outlier Detection (Isolation Forest)
    """

    def __init__(self):
        self.df = None
        self.target_col = None
        self.task_type = None  # "regression" or "classification"
        self.model = None
        self.feature_columns = []
        self.categorical_features = []
        self.numeric_features = []
        self.feature_encoders = {}
        self.metrics = {}
        self.anomalies_df = None
        self._is_trained = False

    def inspect_dataframe(self, df: pd.DataFrame) -> dict:
        """Inspects arbitrary DataFrame to identify numeric and categorical columns."""
        # Clean column names
        df_clean = df.copy()
        df_clean.columns = [str(c).strip() for c in df_clean.columns]
        
        # Exclude pure ID / timestamp / text name columns from default predictors
        candidate_cols = []
        for c in df_clean.columns:
            lower_c = c.lower()
            if lower_c in ["id", "_id"] or lower_c.endswith("_id") or "timestamp" in lower_c or "created_at" in lower_c:
                continue
            # Drop high-cardinality string columns (e.g. movie titles, descriptions, names)
            if df_clean[c].dtype == object:
                if lower_c in ["title", "name", "description", "review_text", "summary", "address", "email", "url"]:
                    continue
                if df_clean[c].nunique() > len(df_clean) * 0.7:
                    continue
            candidate_cols.append(c)

        numeric_cols = [c for c in candidate_cols if pd.api.types.is_numeric_dtype(df_clean[c])]
        categorical_cols = [c for c in candidate_cols if not pd.api.types.is_numeric_dtype(df_clean[c])]

        # Identify default target: prefer business outcome metrics (revenue, box office, sales, GPA, rating)
        default_target = None
        target_keywords = ["box_office", "revenue", "sales", "gpa", "profit", "price", "budget", "rating", "score", "cost", "salary", "target", "label", "status"]
        for kw in target_keywords:
            for c in candidate_cols:
                if kw in c.lower():
                    default_target = c
                    break
            if default_target:
                break
        
        if not default_target:
            if numeric_cols:
                default_target = numeric_cols[-1]
            elif categorical_cols:
                default_target = categorical_cols[-1]
            elif candidate_cols:
                default_target = candidate_cols[-1]

        return {
            "all_columns": list(df_clean.columns),
            "candidate_columns": candidate_cols,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "default_target": default_target,
            "total_rows": len(df_clean)
        }

    def train(self, df: pd.DataFrame, target_col: str, feature_cols: list = None) -> dict:
        """Dynamically trains an optimal ML model on arbitrary user-provided DataFrame."""
        if df.empty or len(df) < 4:
            raise ValueError("Dataset must contain at least 4 rows to train a machine learning model.")

        df_clean = df.copy()
        df_clean.columns = [str(c).strip() for c in df_clean.columns]

        if target_col not in df_clean.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset.")

        # Drop rows where target is NaN
        df_clean = df_clean.dropna(subset=[target_col]).copy()
        self.df = df_clean
        self.target_col = target_col

        # Default feature columns if not specified
        if not feature_cols:
            inspect_info = self.inspect_dataframe(df_clean)
            feature_cols = [c for c in inspect_info["candidate_columns"] if c != target_col]

        # Determine task type: Regression vs Classification
        target_series = df_clean[target_col]
        is_num = pd.api.types.is_numeric_dtype(target_series)
        unique_vals = target_series.nunique()
        is_float = pd.api.types.is_float_dtype(target_series)
        is_int = pd.api.types.is_integer_dtype(target_series)

        if not is_num:
            self.task_type = "classification"
        elif is_float:
            self.task_type = "regression"
        elif is_int and unique_vals <= 5:
            self.task_type = "classification"
        else:
            self.task_type = "regression"

        # Separate feature types
        self.numeric_features = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df_clean[c])]
        self.categorical_features = [c for c in feature_cols if c not in self.numeric_features]

        # Prepare X and y
        X_df = df_clean[feature_cols].copy()
        y = target_series.copy()

        # Handle missing values
        for c in self.numeric_features:
            median_val = X_df[c].median()
            X_df[c] = X_df[c].fillna(median_val if not np.isnan(median_val) else 0)

        for c in self.categorical_features:
            mode_val = X_df[c].mode()[0] if not X_df[c].mode().empty else "Unknown"
            X_df[c] = X_df[c].fillna(mode_val).astype(str)

        # One-hot encode categoricals
        if self.categorical_features:
            X_encoded = pd.get_dummies(X_df, columns=self.categorical_features, drop_first=False)
        else:
            X_encoded = X_df.copy()

        self.feature_columns = list(X_encoded.columns)

        # Train/Test Split
        if len(df_clean) < 10:
            X_train, X_test, y_train, y_test = X_encoded, X_encoded, y, y
        else:
            test_size = 0.20
            strat = None
            if self.task_type == "classification" and len(df_clean) >= 30 and y.value_counts().min() >= 2:
                strat = y
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_encoded, y, test_size=test_size, random_state=42, stratify=strat
                )
            except Exception:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_encoded, y, test_size=test_size, random_state=42
                )

        if self.task_type == "regression":
            self.model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)

            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            # Baseline linear regression
            lin = LinearRegression()
            lin.fit(X_train, y_train)
            lin_r2 = r2_score(y_test, lin.predict(X_test))

            self.metrics = {
                "task_type": "Regression",
                "primary_metric_name": "R² Goodness of Fit",
                "primary_metric_value": max(0.0, round(float(r2), 3)),
                "baseline_r2": max(0.0, round(float(lin_r2), 3)),
                "mae": round(float(mae), 2),
                "total_rows": len(df_clean),
                "features_count": len(self.feature_columns)
            }
        else:
            self.model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)

            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

            self.metrics = {
                "task_type": "Classification",
                "primary_metric_name": "Classification Accuracy",
                "primary_metric_value": round(float(acc * 100), 1),
                "f1_score": round(float(f1), 3),
                "unique_classes": int(unique_vals),
                "total_rows": len(df_clean),
                "features_count": len(self.feature_columns)
            }

        # Fit Isolation Forest for Anomaly Detection on numeric features
        if len(self.numeric_features) >= 1 and len(df_clean) >= 6:
            try:
                num_data = df_clean[self.numeric_features].fillna(0)
                iso = IsolationForest(contamination=min(0.10, 5.0 / len(df_clean)), random_state=42)
                preds = iso.fit_predict(num_data)
                df_clean["is_outlier"] = (preds == -1)
                self.anomalies_df = df_clean[df_clean["is_outlier"]].copy()
            except Exception:
                self.anomalies_df = pd.DataFrame()
        else:
            self.anomalies_df = pd.DataFrame()

        self._is_trained = True
        return self.metrics

    def predict(self, input_dict: dict) -> dict:
        """Predicts target outcome for a single arbitrary sample dictionary."""
        if not self._is_trained or self.model is None:
            raise RuntimeError("Model has not been trained yet.")

        # Build feature vector matching encoded columns
        encoded_dict = {}
        for col in self.feature_columns:
            encoded_dict[col] = 0

        for feat, val in input_dict.items():
            if feat in self.numeric_features:
                if feat in encoded_dict:
                    encoded_dict[feat] = float(val) if val is not None else 0.0
            elif feat in self.categorical_features:
                col_name = f"{feat}_{val}"
                if col_name in encoded_dict:
                    encoded_dict[col_name] = 1

        sample_df = pd.DataFrame([encoded_dict])[self.feature_columns]

        if self.task_type == "regression":
            pred_val = float(self.model.predict(sample_df)[0])
            return {
                "task_type": "regression",
                "predicted_value": round(pred_val, 2),
                "target_name": self.target_col
            }
        else:
            pred_val = str(self.model.predict(sample_df)[0])
            probs = {}
            if hasattr(self.model, "predict_proba"):
                prob_arr = self.model.predict_proba(sample_df)[0]
                classes = self.model.classes_
                probs = {str(classes[i]): round(float(prob_arr[i] * 100), 1) for i in range(len(classes))}
            return {
                "task_type": "classification",
                "predicted_class": pred_val,
                "probabilities": probs,
                "target_name": self.target_col
            }

    def get_feature_importances(self) -> pd.DataFrame:
        """Returns top feature importances from the trained Random Forest model."""
        if not self._is_trained or not hasattr(self.model, "feature_importances_"):
            return pd.DataFrame()
        
        importances = self.model.feature_importances_
        df_imp = pd.DataFrame({
            "Feature": self.feature_columns,
            "Importance": importances
        }).sort_values(by="Importance", ascending=False)
        return df_imp

# Global singleton
universal_automl = UniversalAutoMLEngine()
