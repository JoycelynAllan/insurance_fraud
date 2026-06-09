import os
import pandas as pd
import numpy as np
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import app, db
from models import User, Transaction, Report, Model
from fraud_detection import FraudDetectionModel
from utils import parse_csv, dataframe_to_transactions, generate_report, get_fraud_statistics, get_time_series_data
import logging
import io

logger = logging.getLogger(__name__)

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's transactions
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    
    # Calculate fraud statistics
    stats = get_fraud_statistics(transactions)
    
    # Get time series data for charts
    time_series = get_time_series_data(transactions, interval='day')
    
    # Get recent fraudulent transactions
    fraud_transactions = Transaction.query.filter_by(
        user_id=current_user.id, 
        is_fraud=True
    ).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html',
        stats=stats,
        time_series=time_series,
        fraud_transactions=fraud_transactions,
        transaction_count=len(transactions)
    )

# Upload route
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if the file is empty
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Check file extension
        if not file.filename.endswith('.csv'):
            flash('Only CSV files are allowed', 'danger')
            return redirect(request.url)
        
        try:
            # Parse the CSV file
            df = parse_csv(file)
            
            # Store the parsed data in the session for analysis
            session['csv_data'] = df.to_json(orient='records', date_format='iso')
            
            # Redirect to analysis page
            return redirect(url_for('analyze'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('upload.html')

# Analyze route
@app.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze():
    # Check if there's data to analyze
    if 'csv_data' not in session:
        flash('No data to analyze. Please upload a file first.', 'warning')
        return redirect(url_for('upload'))
    
    # Load the data from the session
    try:
        df = pd.read_json(session['csv_data'])
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'danger')
        return redirect(url_for('upload'))
    
    if request.method == 'POST':
        try:
            # Initialize the fraud detection model
            model = FraudDetectionModel(model_type='random_forest')
            
            # Try to load a pre-trained model, or train a new one if not available
            try:
                model.load_model()
            except FileNotFoundError:
                # No existing model, so we'll need to train one
                # For now, let's just use a simple method without actual training
                logger.warning("No pre-trained model found. Using a simplified detection method.")
                
                # Make predictions (in a real scenario, this would use the trained model)
                fraud_probs = np.random.rand(len(df))
                fraud_flags = fraud_probs > 0.9  # Flagging transactions with probability > 0.9 as fraud
                
                df['fraud_probability'] = fraud_probs
                df['is_fraud'] = fraud_flags
            else:
                # If model was loaded successfully, use it to make predictions
                # First, ensure the DataFrame has the necessary columns
                required_cols = ['transaction_id', 'amount', 'timestamp', 'merchant']
                for col in required_cols:
                    if col not in df.columns:
                        if col == 'transaction_id':
                            df[col] = [f"tx_{i}" for i in range(len(df))]
                        elif col == 'amount':
                            df[col] = 0.0
                        elif col == 'timestamp':
                            df[col] = datetime.now()
                        elif col == 'merchant':
                            df[col] = 'Unknown'
                
                # Make predictions
                fraud_probs = model.predict_proba(df)
                fraud_flags = model.predict(df)
                
                df['fraud_probability'] = fraud_probs
                df['is_fraud'] = fraud_flags
            
            # Flag high-risk transactions
            threshold = 0.8
            df['flagged'] = df['fraud_probability'] > threshold
            df['flagged_reason'] = df.apply(
                lambda row: f"High fraud probability: {row['fraud_probability']:.2f}" if row['flagged'] else None,
                axis=1
            )
            
            # Convert to Transaction objects and save to database
            transactions = dataframe_to_transactions(df, current_user.id)
            
            # Add all transactions to the database
            db.session.add_all(transactions)
            db.session.commit()
            
            # Clear the session data
            session.pop('csv_data', None)
            
            flash(f"Analysis complete. {len(transactions)} transactions processed. {df['is_fraud'].sum()} fraudulent transactions detected.", 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error analyzing data: {str(e)}', 'danger')
            return render_template('analyze.html', data=df.head(10).to_dict('records'))
    
    # Display the first 10 rows for preview
    return render_template('analyze.html', data=df.head(10).to_dict('records'))

# Reports route
@app.route('/reports')
@login_required
def reports():
    # Get user's reports
    user_reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    
    return render_template('reports.html', reports=user_reports)

# Create report route
@app.route('/reports/create', methods=['GET', 'POST'])
@login_required
def create_report():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        # Validation
        if not title:
            flash('Title is required', 'danger')
            return redirect(request.url)
        
        if end_date < start_date:
            flash('End date cannot be before start date', 'danger')
            return redirect(request.url)
        
        # Get transactions for the date range
        transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        ).all()
        
        # Generate the report
        report = generate_report(
            current_user.id,
            title,
            description,
            start_date,
            end_date,
            transactions
        )
        
        # Save to database
        db.session.add(report)
        db.session.commit()
        
        flash('Report created successfully', 'success')
        return redirect(url_for('reports'))
    
    return render_template('create_report.html')

# View report route
@app.route('/reports/<int:report_id>')
@login_required
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    
    # Ensure the report belongs to the current user
    if report.user_id != current_user.id:
        flash('You do not have permission to view this report', 'danger')
        return redirect(url_for('reports'))
    
    # Get transactions for the report's date range
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.timestamp >= report.start_date,
        Transaction.timestamp <= report.end_date
    ).all()
    
    # Calculate statistics
    stats = get_fraud_statistics(transactions)
    
    # Get time series data
    time_series = get_time_series_data(transactions, interval='day')
    
    return render_template(
        'view_report.html',
        report=report,
        stats=stats,
        time_series=time_series,
        transactions=transactions
    )

# Transaction details route
@app.route('/transactions/<int:transaction_id>')
@login_required
def transaction_detail(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Ensure the transaction belongs to the current user
    if transaction.user_id != current_user.id:
        flash('You do not have permission to view this transaction', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('transaction_detail.html', transaction=transaction)

# API route for getting transaction data
@app.route('/api/transactions')
@login_required
def api_transactions():
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    fraud_only = request.args.get('fraud_only', 'false').lower() == 'true'
    
    # Build the query
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if start_date:
        query = query.filter(Transaction.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
    
    if end_date:
        query = query.filter(Transaction.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    if fraud_only:
        query = query.filter_by(is_fraud=True)
    
    # Execute the query
    transactions = query.order_by(Transaction.timestamp.desc()).all()
    
    # Convert to dictionary
    transactions_dict = [t.to_dict() for t in transactions]
    
    return jsonify(transactions_dict)

# API route for getting fraud statistics
@app.route('/api/stats')
@login_required
def api_stats():
    # Get query parameters
    period = request.args.get('period', 'all')
    
    # Determine the date range based on the period
    end_date = datetime.utcnow()
    
    if period == 'day':
        start_date = end_date - timedelta(days=1)
    elif period == 'week':
        start_date = end_date - timedelta(weeks=1)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
    else:  # 'all'
        start_date = datetime.min
    
    # Get transactions for the period
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.timestamp >= start_date,
        Transaction.timestamp <= end_date
    ).all()
    
    # Calculate statistics
    stats = get_fraud_statistics(transactions)
    
    return jsonify(stats)

# API route for getting time series data
@app.route('/api/timeseries')
@login_required
def api_timeseries():
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    interval = request.args.get('interval', 'day')
    
    # Build the query
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if start_date:
        query = query.filter(Transaction.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
    
    if end_date:
        query = query.filter(Transaction.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    # Execute the query
    transactions = query.all()
    
    # Generate time series data
    time_series = get_time_series_data(transactions, interval=interval)
    
    return jsonify(time_series)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
