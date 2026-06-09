# AI-Enabled Fraud Detection System


An advanced machine learning-powered system for detecting fraudulent financial transactions. Features interactive dashboards, real-time analysis, and secure user authentication.

🌐 [Live Demo](https://adithya17-star.github.io/AI-Powered-Fraud-Detection/)

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![GitHub Pages](https://img.shields.io/badge/Deployed-GitHub--Pages-brightgreen)

## 🔍 Features

- **Machine Learning Detection**: Detects suspicious activity using Random Forest and Isolation Forest algorithms
- **Interactive Dashboard**: Real-time statistics and visualization of transaction data
- **CSV Upload & Analysis**: Upload transaction data and analyze with custom sensitivity
- **Comprehensive Reports**: Generate detailed fraud analysis reports with visualizations
- **Transaction Deep Dive**: View risk factors and breakdowns for each transaction
- **User Authentication**: Secure registration, login, and session management

## 🛠️ Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Machine Learning**: scikit-learn, pandas, NumPy
- **Frontend**: Bootstrap, Chart.js, JavaScript
- **Authentication**: Flask-Login

## 📋 Requirements

- Python 3.10+
- PostgreSQL database
- Modern web browser

## 🚀 Installation

1. Clone the repository
```bash
git clone https://github.com/Adithya17-star/AI-Enabled-Fraud-Detection.git
cd AI-Enabled-Fraud-Detection
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables
```
DATABASE_URL=postgresql://username:password@localhost:5432/fraud_detection
SESSION_SECRET=your-secure-secret-key
```

4. Initialize the database
```bash
python -c "from app import db; db.create_all()"
```

5. Run the application
```bash
python main.py
```

6. Open your browser and navigate to `http://localhost:5000`

## 📊 Usage Guide

### Registration & Login
1. Create a new account via the Registration page
2. Log in using your credentials

### Uploading Transactions
1. Navigate to the Upload page
2. Upload a CSV file with transaction data (see format below)
3. Preview the data and start analysis

### Transaction CSV Format
Your CSV file should include the following columns:
- `transaction_id`: Unique identifier
- `amount`: Transaction amount
- `timestamp`: Date and time (YYYY-MM-DD HH:MM:SS)
- `merchant`: Merchant name
- `merchant_category`: Category of merchant (optional)
- `description`: Transaction description (optional)
- `location`: Transaction location (optional)
- `ip_address`: IP address (optional)
- `device_id`: Device identifier (optional)

### Analyzing Transactions
1. Select detection model (Random Forest or Isolation Forest)
2. Adjust detection sensitivity
3. Start analysis to identify fraudulent transactions

### Dashboard
- View key metrics including total transactions, fraud count, and amounts
- Analyze transaction trends over time
- Examine fraud distribution by merchant category

### Reports
1. Create a new report by specifying date range and title
2. View detailed fraud patterns and statistics
3. Export reports for record-keeping

## 📝 Project Structure

```
AI-Enabled-Fraud-Detection/
├── static/                     # Static assets
│   ├── css/                    # CSS stylesheets
│   └── js/                     # JavaScript files
├── templates/                  # HTML templates
├── app.py                      # Flask application setup
├── main.py                     # Application entry point
├── models.py                   # Database models
├── routes.py                   # Application routes
├── fraud_detection.py          # Fraud detection algorithms
├── data_preprocessing.py       # Data preprocessing utilities
└── utils.py                    # Helper functions
```

## 🔒 Security Considerations

- All passwords are securely hashed using werkzeug's security functions
- PostgreSQL database with secure connection
- Input validation on all form submissions
- Session management via Flask-Login

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Adithya Kakarla** - *Initial work* - [Adithya17-star](https://github.com/Adithya17-star)

## 🙏 Acknowledgements

- [Bootstrap](https://getbootstrap.com/) for the UI components
- [Chart.js](https://www.chartjs.org/) for data visualization
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [scikit-learn](https://scikit-learn.org/) for machine learning capabilities

---

This project is part of an ongoing effort to improve fraud detection systems using artificial intelligence and machine learning techniques.
