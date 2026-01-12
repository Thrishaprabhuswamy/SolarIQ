# ☀️ SolarIQ — Smart Solar Energy Monitoring Dashboard

SolarIQ is a full-stack web application that visualizes **solar energy production and consumption** in real-time, with predictive analytics powered by **Flask + Prophet (Python)** and a modern **EJS + Express frontend**.  

It provides beautiful **Chart.js visualizations**, **live metrics**, and **forecast insights** to help optimize solar usage and energy storage.

---

## Features

### **Dashboard Overview**
- Real-time combined chart for **Solar vs Load** data  
- Separate charts for **Solar Data** and **Load Data** (past + predicted)  
- Predictive analytics using machine learning forecasts (Prophet model)  
- Glassmorphism-inspired responsive UI with TailwindCSS  

## **Metrics Display**
- Solar energy produced (kWh)
- Energy consumed (kWh)
- Peak voltage (V) and current (A)
- Net energy prediction (Generated − Consumed)

### **Prediction System**
- Fetches real-time historical and forecast data from Flask backend  
- Supports manual date range input (`Start Date` & `End Date`)
- Displays dummy data automatically if Flask is offline  

### **Fallback Mode**
- When Flask isn’t connected, the dashboard auto-generates **dummy solar/load data** for demonstration.

## Credits
This project was developed as part of a hackathon team effort.
Original repository by aananyaph.

---



