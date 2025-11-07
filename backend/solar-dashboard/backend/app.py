from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from prophet import Prophet
import os
import requests
import pickle

app = Flask(__name__)
CORS(app)

DB_PATH = "predictions.db"
os.makedirs("models", exist_ok=True)

# ============================================
# 💰 Tariff Configurations
# ============================================
TARIFFS = {
    "domestic": 5.8,
    "institution": 6.3,
    "industry": 7.5,
}

SOLAR_TARIFFS = {
    "domestic_no_subsidy": 4.15,
    "pm_surya_1_2kw": 2.30,
    "pm_surya_2_3kw": 2.48,
    "pm_surya_above_3kw": 2.93,
    "non_domestic": 3.08,
    "mw_ground": 3.07,
}

# ============================================
# 📊 Utility: Lag features for self-learning Prophet
# ============================================
def add_lag_features(df, col="y", lags=3):
    for i in range(1, lags + 1):
        df[f"{col}_lag_{i}"] = df[col].shift(i)
    df.dropna(inplace=True)
    return df

# ============================================
# 🔮 Prophet forecast helper
# ============================================
def train_and_forecast(df, target_col, model_path, periods=30):
    df = df.rename(columns={target_col: "y", "date": "ds"})
    df = add_lag_features(df, "y", 3)

    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    else:
        model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)

    model.fit(df)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    forecast["ds"] = pd.to_datetime(forecast["ds"])
    return forecast[["ds", "yhat"]]

# ============================================
# 🧩 Database Initialization
# ============================================
def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    ds TEXT,
                    yhat REAL
                )
            """)
            conn.commit()
        print("✅ Database initialized")

init_db()

# ============================================
# ☀️ Today's Summary (used by /today_status)
# ============================================
def get_today_data():
    today = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM predictions", conn)

    df_today = df[df["ds"].str.startswith(today)] if not df.empty else pd.DataFrame()
    if df_today.empty:
        return {"status": "no_data", "date": today, "total_energy": 0, "peak_power": 0, "avg_efficiency": 0}

    total_energy = round(df_today["yhat"].sum(), 2)
    peak_power = round(df_today["yhat"].max(), 2)
    avg_efficiency = round((df_today["yhat"].mean() / (peak_power or 1)) * 100, 2)

    return {"status": "success", "date": today, "total_energy": total_energy, "peak_power": peak_power, "avg_efficiency": avg_efficiency}

# ============================================
# 🛰️ NASA DATA
# ============================================
@app.route("/nasa_data")
def nasa_data():
    lat = request.args.get("lat", 12.97, type=float)
    lon = request.args.get("lon", 77.59, type=float)
    start = request.args.get("start", (datetime.now()-timedelta(days=7)).strftime("%Y%m%d"))
    end = request.args.get("end", datetime.now().strftime("%Y%m%d"))

    nasa_url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=ALLSKY_SFC_SW_DWN,T2M,WIND_SPEED&community=RE"
        f"&longitude={lon}&latitude={lat}&start={start}&end={end}&format=JSON"
    )
    try:
        res = requests.get(nasa_url)
        res.raise_for_status()
        data = res.json()
        params = data["properties"]["parameter"]
        df = pd.DataFrame({
            "date": list(params["ALLSKY_SFC_SW_DWN"].keys()),
            "solar_irradiance": list(params["ALLSKY_SFC_SW_DWN"].values()),
            "temperature": list(params["T2M"].values()),
            "wind_speed": list(params["WIND_SPEED"].values())
        })
        return jsonify({"status": "success", "data": df.to_dict(orient="records")})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# 📊 HISTORY (Dummy Data)
# ============================================
@app.route("/history")
def history():
    date_rng = pd.date_range(end=datetime.now(), periods=30)
    df = pd.DataFrame({
        "date": date_rng.strftime("%Y-%m-%d"),
        "solar": np.random.uniform(10, 25, len(date_rng)),
        "load": np.random.uniform(18, 35, len(date_rng))
    })
    return jsonify(df.to_dict(orient="records"))

# ============================================
# 🌞 TODAY STATUS
# ============================================
@app.route("/today_status")
def today_status():
    try:
        return jsonify(get_today_data())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ============================================
# 💸 SOLAR BILLING STATUS
# ============================================
@app.route("/solar_status")
def solar_status():
    category = request.args.get("category", "domestic")
    avg_power = float(request.args.get("avg_power", 5))

    solar_generation = np.random.uniform(15, 25)
    grid_import = np.random.uniform(10, 20)
    grid_export = np.random.uniform(0, 5)

    net_grid_consumption = grid_import - grid_export
    total_consumption = solar_generation + net_grid_consumption

    # Select tariffs
    if category == "domestic":
        if avg_power <= 2:
            solar_tariff = SOLAR_TARIFFS["pm_surya_1_2kw"]
        elif 2 < avg_power <= 3:
            solar_tariff = SOLAR_TARIFFS["pm_surya_2_3kw"]
        elif 3 < avg_power <= 10:
            solar_tariff = SOLAR_TARIFFS["pm_surya_above_3kw"]
        else:
            solar_tariff = SOLAR_TARIFFS["domestic_no_subsidy"]
    elif category in ["institution", "industry"]:
        solar_tariff = SOLAR_TARIFFS["non_domestic"]
    else:
        solar_tariff = SOLAR_TARIFFS["mw_ground"]

    grid_tariff = TARIFFS.get(category, 5.8)

    normal_bill = total_consumption * grid_tariff
    solar_bill = max(0, net_grid_consumption * grid_tariff)
    solar_gen_cost = solar_generation * solar_tariff
    savings = normal_bill - (solar_bill + solar_gen_cost)

    peak_voltage = np.random.uniform(210, 240)
    peak_current = np.random.uniform(8, 12)
    peak_power = round((peak_voltage * peak_current) / 1000, 2)

    return jsonify({
        "category": category,
        "solar_generation": round(solar_generation, 2),
        "grid_import": round(grid_import, 2),
        "grid_export": round(grid_export, 2),
        "net_grid_consumption": round(net_grid_consumption, 2),
        "total_consumption": round(total_consumption, 2),
        "grid_tariff": grid_tariff,
        "solar_tariff": solar_tariff,
        "normal_bill": round(normal_bill, 2),
        "solar_bill": round(solar_bill, 2),
        "solar_generation_cost": round(solar_gen_cost, 2),
        "savings": round(savings, 2),
        "peak_voltage": round(peak_voltage, 2),
        "peak_current": round(peak_current, 2),
        "peak_power": peak_power
    })

# ============================================
# 🔮 PREDICT (Self-Learning Forecast)
# ============================================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        req = request.get_json(force=True)
        start = req.get("start_date")
        end = req.get("end_date")

        if not start or not end:
            return jsonify({"status": "error", "message": "Missing start or end date"}), 400

        date_rng = pd.date_range(datetime.now() - timedelta(days=180), periods=180)
        df = pd.DataFrame({
            "date": date_rng,
            "solar": np.random.uniform(10, 25, len(date_rng)),
            "load": np.random.uniform(15, 30, len(date_rng))
        })

        solar_forecast = train_and_forecast(df[["date", "solar"]].copy(), "solar", "models/solar_model.pkl", periods=30)
        load_forecast = train_and_forecast(df[["date", "load"]].copy(), "load", "models/load_model.pkl", periods=30)

        merged = pd.merge(solar_forecast, load_forecast, on="ds", suffixes=("_solar", "_load"))
        merged = merged[(merged["ds"] >= pd.to_datetime(start)) & (merged["ds"] <= pd.to_datetime(end))]

        if merged.empty:
            return jsonify({"status": "success", "predictions": []})

        return jsonify({"status": "success", "predictions": merged.to_dict(orient="records")})
    except Exception as e:
        import traceback
        print("❌ Predict error:", traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# 🧪 Root Health
# ============================================
@app.route("/")
def home():
    return jsonify({
        "message": "✅ SolarIQ Flask backend active",
        "routes": ["/history", "/today_status", "/solar_status", "/predict", "/nasa_data"]
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)