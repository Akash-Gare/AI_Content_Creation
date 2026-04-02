import os
import joblib
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy import text
from app.database.db import engine, SessionLocal
from app.database.models import PosterRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = "app/ml/timing_model.joblib"

def fetch_data():
    """Fetch historical posting data from PostgreSQL."""
    db = SessionLocal()
    try:
        # Fetch only posted items with engagement metrics
        query = db.query(PosterRequest).filter(
            PosterRequest.status == "Posted",
            PosterRequest.posted_at.isnot(None)
        ).all()
        
        if not query:
            logger.warning("No historical data found for training.")
            return None
        
        data = []
        for row in query:
            data.append({
                "posted_at": row.posted_at,
                "likes": row.likes or 0,
                "views": row.views or 0,
                "engagement": (row.likes or 0) + (row.views or 0) * 0.1 # Example engagement score
            })
        
        return pd.DataFrame(data)
    finally:
        db.close()

def preprocess(df):
    """Extract features: hour and day of week."""
    if df is None or df.empty:
        return None, None
    
    df['hour'] = df['posted_at'].dt.hour
    df['day_of_week'] = df['posted_at'].dt.dayofweek
    
    X = df[['hour', 'day_of_week']]
    y = df['engagement']
    return X, y

def train_model():
    """Train the RandomForest model and save it."""
    logger.info("Retraining timing model...")
    df = fetch_data()
    X, y = preprocess(df)
    
    if X is None or len(X) < 5: # Need a minimum amount of data
        logger.warning("Insufficient data to train model. Minimum 5 records required.")
        return False
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")
    return True

def predict_best_time():
    """Predict the best hour to post today."""
    if not os.path.exists(MODEL_PATH):
        logger.info("Model not found. Using default hour (18:00).")
        return 18
    
    try:
        model = joblib.load(MODEL_PATH)
        today = datetime.now()
        day_of_week = today.weekday()
        
        # Predict engagement for each hour (0-23)
        hours = list(range(24))
        X_pred = pd.DataFrame({
            'hour': hours,
            'day_of_week': [day_of_week] * 24
        })
        
        predictions = model.predict(X_pred)
        best_hour = hours[predictions.argmax()]
        
        logger.info(f"Predicted best posting hour: {best_hour}:00 (Score: {max(predictions):.2f})")
        return int(best_hour)
    except Exception as e:
        logger.error(f"Prediction failed: {e}. Defaulting to 18:00.")
        return 18

if __name__ == "__main__":
    # Test training
    train_model()
    # Test prediction
    print(f"Best hour: {predict_best_time()}")
