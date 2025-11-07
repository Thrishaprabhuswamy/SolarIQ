# Solar Dashboard

## Overview
The Solar Dashboard is a web application that provides insights into solar energy generation and consumption. It utilizes data from NASA's satellite services and forecasts energy loads to help users understand their solar energy usage and savings.

## Project Structure
```
solar-dashboard
├── backend
│   ├── app.py                # Main application file for the Flask backend
│   ├── requirements.txt      # Python dependencies for the project
│   ├── models                # Directory for storing machine learning models
│   │   └── .gitkeep          # Keeps the models directory tracked by Git
│   ├── templates             # HTML templates for the dashboard
│   │   └── dashboard.html     # Main dashboard HTML file
│   └── static                # Static files (CSS, JS)
│       ├── css
│       │   └── styles.css    # CSS styles for the dashboard
│       └── js
│           ├── dashboard.js   # JavaScript for handling user interactions
│           └── charts.js      # JavaScript for rendering charts
├── .gitignore                # Files and directories to ignore by Git
└── README.md                 # Documentation for the project
```

## Setup Instructions
1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd solar-dashboard
   ```

2. **Install dependencies**:
   It is recommended to use a virtual environment. You can create one using:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
   Then install the required packages:
   ```
   pip install -r backend/requirements.txt
   ```

3. **Run the backend**:
   Navigate to the `backend` directory and run the Flask application:
   ```
   python app.py
   ```

4. **Access the dashboard**:
   Open your web browser and go to `http://127.0.0.1:5000` to view the dashboard.

## Usage
- The dashboard allows users to input a start date and an end date to filter the data displayed in the graphs.
- Users can view historical solar generation data, load data, and predictions based on the specified date range.
- The application fetches data from NASA's API and processes it to provide insights into solar energy usage.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.