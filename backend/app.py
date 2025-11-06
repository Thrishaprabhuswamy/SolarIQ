from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from prophet import Prophet
import lightgbm as lgb
import numpy as np
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =======================================================
# 🧩 DATABASE SETUP (SQLite)
# =======================================================
DB_PATH = "predictions.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                yhat_solar REAL,
                yhat_load REAL,
                net_demand REAL,
                created_at TEXT
            )
        """)
init_db()

# =======================================================
# 📊 SAMPLE DATASET GENERATOR
# =======================================================
def load_dataset():
    rng = pd.date_range("2025-01-01", periods=180, freq="D")
    df = pd.DataFrame({
        "ds": rng,
        "solar": np.clip(
            400 + 50 * np.sin(np.linspace(0, 3*np.pi, 180)) + np.random.randn(180)*10,
            300, 600
        ),
        "load": np.clip(
            380 + 40 * np.cos(np.linspace(0, 2*np.pi, 180)) + np.random.randn(180)*8,
            300, 500
        ),
    })
    return df


# =======================================================
# 🔮 PREDICT ENDPOINT (Prophet + LightGBM)
# =======================================================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if not start_date or not end_date:
            return jsonify({"error": "Missing start_date or end_date"}), 400

        df = load_dataset()

        # 1️⃣ Prophet → Solar Forecast
        df_solar = df.rename(columns={"ds": "ds", "solar": "y"})
        model_solar = Prophet(daily_seasonality=True)
        model_solar.fit(df_solar)
        future_solar = model_solar.make_future_dataframe(
            periods=(pd.to_datetime(end_date) - df["ds"].max()).days, freq="D"
        )
        forecast_solar = model_solar.predict(future_solar)[["ds", "yhat"]]
        forecast_solar.rename(columns={"yhat": "yhat_solar"}, inplace=True)

        # 2️⃣ LightGBM → Load Forecast
        df["day_of_year"] = df["ds"].dt.dayofyear
        df["solar_prev"] = df["solar"].shift(1).bfill()
        X = df[["day_of_year", "solar_prev"]]
        y = df["load"]

        train_data = lgb.Dataset(X, label=y)
        params = {"objective": "regression", "verbosity": -1, "metric": "rmse"}
        model_load = lgb.train(params, train_data, num_boost_round=80)

        future_days = pd.date_range(start=start_date, end=end_date, freq="D")
        future_df = pd.DataFrame({"ds": future_days})
        future_df["day_of_year"] = future_df["ds"].dt.dayofyear
        future_df["solar_prev"] = np.clip(
            450 + 30 * np.sin(np.linspace(0, np.pi, len(future_days))),
            300, 600
        )
        yhat_load = model_load.predict(future_df[["day_of_year", "solar_prev"]])
        forecast_load = pd.DataFrame({"ds": future_df["ds"], "yhat_load": yhat_load})

        # 3️⃣ Merge only overlapping forecast dates
        merged = pd.merge(forecast_solar, forecast_load, on="ds", how="inner")

        # ✅ Compute net demand safely
        merged["net_demand"] = merged["yhat_load"] - merged["yhat_solar"]

        # ✅ Filter between user-selected range
        mask = (merged["ds"] >= pd.to_datetime(start_date)) & (merged["ds"] <= pd.to_datetime(end_date))
        merged = merged.loc[mask].dropna(subset=["yhat_solar", "yhat_load", "net_demand"])

        # ✅ Round values for cleaner output
        merged = merged.round(2)

        # 4️⃣ Save results to SQLite
        with sqlite3.connect(DB_PATH) as conn:
            for _, row in merged.iterrows():
                conn.execute("""
                    INSERT INTO forecasts (date, yhat_solar, yhat_load, net_demand, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row["ds"].strftime("%Y-%m-%d"),
                    float(row["yhat_solar"]),
                    float(row["yhat_load"]),
                    float(row["net_demand"]),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
            conn.commit()

        print(f"✅ Stored {len(merged)} new predictions.")
        return jsonify(merged.to_dict(orient="records"))

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500


# =======================================================
# 📜 HISTORY ENDPOINT
# =======================================================
@app.route("/history", methods=["GET"])
def history():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("""
                SELECT date, yhat_solar, yhat_load, net_demand, created_at
                FROM forecasts
                ORDER BY date DESC
                LIMIT 100
            """).fetchall()

        data = [
            {
                "date": r[0],
                "yhat_solar": r[1],
                "yhat_load": r[2],
                "net_demand": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]
        return jsonify(data)
    except Exception as e:
        print("❌ History Error:", e)
        return jsonify({"error": str(e)}), 500


# =======================================================
# 🚀 RUN SERVER
# =======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
