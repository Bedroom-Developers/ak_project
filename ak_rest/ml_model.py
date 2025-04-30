import os
import joblib
import pandas as pd
import numpy as np
from django.db.models import F
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime

from .models import Requests, Details

MODEL_PATH = "ml_model.pkl"

def train_model():
    # Извлекаем только завершённые заказы
    data = Requests.objects.filter(status="Done").annotate(
        measurement_date=F('details__measurement_date')
    ).values('id', 'width', 'height', 'window_type', 'price', 'created_at', 'measurement_date')

    df = pd.DataFrame(list(data))
    if df.empty:
        return "Недостаточно данных для обучения."

    # Преобразуем даты в числовой формат
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
    df['measurement_date'] = pd.to_datetime(df['measurement_date']).dt.tz_localize(None)
    
    # Целевая переменная — разница между датой замера и датой создания заказа
    df['days_to_complete'] = (df['measurement_date'] - df['created_at']).dt.days

    # Удаляем заказы без даты замера
    df.dropna(subset=['days_to_complete'], inplace=True)

    # One-hot encoding для типа окна
    df = pd.get_dummies(df, columns=['window_type'], drop_first=True)

    # Формируем данные для модели
    X = df.drop(columns=['id', 'measurement_date', 'days_to_complete'])
    y = df['days_to_complete']

    # Разделяем на train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Обучаем модель
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Оцениваем точность
    y_pred = model.predict(X_test)
    print("MAE:", mean_absolute_error(y_test, y_pred))
    print("RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))

    # Сохраняем модель
    joblib.dump(model, MODEL_PATH)
    return "Модель обучена и сохранена!"

def predict_completion_date(request_id):
    if not os.path.exists(MODEL_PATH):
        return {"error": "Модель не обучена. Сначала запусти обучение."}

    model = joblib.load(MODEL_PATH)

    # Достаем данные по конкретному заказу
    request_data = Requests.objects.filter(id=request_id).values(
        'width', 'height', 'window_type', 'price', 'created_at'
    ).first()

    if not request_data:
        return {"error": "Заказ не найден."}

    df = pd.DataFrame([request_data])
    df['created_at'] = datetime.now().timestamp()

    # One-hot encoding
    df = pd.get_dummies(df, columns=['window_type'], drop_first=True)

    # Добавляем недостающие колонки (если в обучении были другие `window_type`)
    for col in model.feature_names_in_:
        if col not in df.columns:
            df[col] = 0

    # Делаем предсказание
    predicted_days = model.predict(df)[0]
    completion_date = datetime.now() + pd.Timedelta(days=predicted_days)

    return {"completion_date": completion_date.strftime('%Y-%m-%d')}

MODEL_PATH_SUCCESS = "success_model.joblib"
SCALER_PATH_SUCCESS = "success_scaler.joblib"


def train_success_model():
    """Функция для обучения модели предсказания успеха заказа"""
    details = Details.objects.select_related("request_id").all()
    data = []

    for detail in details:
        data.append({
            "worker_id": detail.worker_id.id if detail.worker_id else 0,
            "width": detail.request_id.width,
            "height": detail.request_id.height,
            "price": detail.request_id.price,
            "window_type": detail.request_id.window_type or "unknown",
            "status": 1 if detail.status == "Done" else 0  # 1 - успех, 0 - неуспех
        })

    df = pd.DataFrame(data)

    if df.empty:
        raise ValueError("Нет данных для обучения")

    df["window_type"] = df["window_type"].astype("category").cat.codes
    df["worker_id"] = df["worker_id"].astype("category").cat.codes

    X = df.drop(columns=["status"])
    y = df["status"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH_SUCCESS)
    joblib.dump(scaler, SCALER_PATH_SUCCESS)


def predict_success(worker_id, width, height, price, window_type):
    """Функция для предсказания успеха заказа"""
    try:
        model = joblib.load(MODEL_PATH_SUCCESS)
        scaler = joblib.load(SCALER_PATH_SUCCESS)
    except FileNotFoundError:
        raise FileNotFoundError("Модель не найдена, обучите её сначала")

    window_type_code = pd.Series([window_type]).astype("category").cat.codes[0]

    X_new = np.array([[worker_id, width, height, price, window_type_code]])
    X_scaled = scaler.transform(X_new)

    success_prob = model.predict_proba(X_scaled)[0][1]  # Вероятность успеха
    return {"success": success_prob > 0.5, "probability": success_prob}