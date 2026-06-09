import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import io
import uuid
from models import Transaction, Report

logger = logging.getLogger(__name__)

def parse_csv(file_obj):
    """
    Parse uploaded CSV file into a pandas DataFrame
    
    Parameters:
    -----------
    file_obj : file-like object
        The uploaded CSV file object
    
    Returns:
    --------
    pandas.DataFrame
        The parsed DataFrame
    """
    try:
        logger.info("Parsing CSV file")
        df = pd.read_csv(file_obj)
        
        # Basic validation
        required_columns = ['transaction_id', 'amount', 'timestamp', 'merchant']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")
            
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"CSV parsed successfully. DataFrame shape: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error parsing CSV: {str(e)}")
        raise

def dataframe_to_transactions(df, user_id):
    """
    Convert DataFrame rows to Transaction objects
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing transaction data
    user_id : int
        ID of the user who uploaded the transactions
    
    Returns:
    --------
    list
        List of Transaction objects
    """
    transactions = []
    
    try:
        logger.info("Converting DataFrame to Transaction objects")
        
        for _, row in df.iterrows():
            # Create a new Transaction object
            transaction = Transaction(
                transaction_id=row.get('transaction_id', str(uuid.uuid4())),
                amount=float(row.get('amount', 0.0)),
                timestamp=row.get('timestamp', datetime.utcnow()),
                merchant=row.get('merchant', 'Unknown'),
                merchant_category=row.get('merchant_category', None),
                description=row.get('description', None),
                location=row.get('location', None),
                ip_address=row.get('ip_address', None),
                device_id=row.get('device_id', None),
                is_fraud=bool(row.get('is_fraud', False)),
                fraud_probability=float(row.get('fraud_probability', 0.0)),
                flagged=bool(row.get('flagged', False)),
                flagged_reason=row.get('flagged_reason', None),
                user_id=user_id
            )
            
            transactions.append(transaction)
        
        logger.info(f"Converted {len(transactions)} rows to Transaction objects")
        return transactions
        
    except Exception as e:
        logger.error(f"Error converting DataFrame to transactions: {str(e)}")
        raise

def generate_report(user_id, title, description, start_date, end_date, transactions):
    """
    Generate a fraud report based on transaction data
    
    Parameters:
    -----------
    user_id : int
        ID of the user creating the report
    title : str
        Report title
    description : str
        Report description
    start_date : datetime
        Start date for the report period
    end_date : datetime
        End date for the report period
    transactions : list
        List of Transaction objects
    
    Returns:
    --------
    Report
        Generated Report object
    """
    try:
        logger.info(f"Generating report: {title}")
        
        # Filter transactions by date range
        filtered_transactions = [t for t in transactions if start_date <= t.timestamp <= end_date]
        
        # Get fraud statistics
        fraud_transactions = [t for t in filtered_transactions if t.is_fraud]
        fraud_count = len(fraud_transactions)
        total_fraud_amount = sum(t.amount for t in fraud_transactions)
        
        # Create report
        report = Report(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            fraud_count=fraud_count,
            total_fraud_amount=total_fraud_amount,
            user_id=user_id
        )
        
        logger.info(f"Report generated: {fraud_count} fraudulent transactions found")
        return report
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise

def get_fraud_statistics(transactions):
    """
    Calculate statistics about fraudulent transactions
    
    Parameters:
    -----------
    transactions : list
        List of Transaction objects
    
    Returns:
    --------
    dict
        Dictionary with fraud statistics
    """
    try:
        logger.info("Calculating fraud statistics")
        
        # Count total and fraudulent transactions
        total_count = len(transactions)
        fraud_count = sum(1 for t in transactions if t.is_fraud)
        
        # Calculate total and fraudulent amounts
        total_amount = sum(t.amount for t in transactions)
        fraud_amount = sum(t.amount for t in transactions if t.is_fraud)
        
        # Calculate fraud percentage
        fraud_percentage = (fraud_count / total_count * 100) if total_count > 0 else 0
        
        # Calculate average transaction amount
        avg_amount = total_amount / total_count if total_count > 0 else 0
        
        # Calculate average fraud amount
        avg_fraud_amount = fraud_amount / fraud_count if fraud_count > 0 else 0
        
        # Group by merchant category
        merchant_categories = {}
        for t in transactions:
            category = t.merchant_category or 'Unknown'
            if category not in merchant_categories:
                merchant_categories[category] = {'count': 0, 'fraud_count': 0}
            
            merchant_categories[category]['count'] += 1
            if t.is_fraud:
                merchant_categories[category]['fraud_count'] += 1
        
        # Calculate fraud rate by merchant category
        for category in merchant_categories:
            cat_count = merchant_categories[category]['count']
            cat_fraud = merchant_categories[category]['fraud_count']
            merchant_categories[category]['fraud_rate'] = (cat_fraud / cat_count * 100) if cat_count > 0 else 0
        
        # Group by location
        locations = {}
        for t in transactions:
            location = t.location or 'Unknown'
            if location not in locations:
                locations[location] = {'count': 0, 'fraud_count': 0}
            
            locations[location]['count'] += 1
            if t.is_fraud:
                locations[location]['fraud_count'] += 1
        
        # Calculate fraud rate by location
        for location in locations:
            loc_count = locations[location]['count']
            loc_fraud = locations[location]['fraud_count']
            locations[location]['fraud_rate'] = (loc_fraud / loc_count * 100) if loc_count > 0 else 0
        
        # Compile statistics
        stats = {
            'total_transactions': total_count,
            'fraud_transactions': fraud_count,
            'total_amount': total_amount,
            'fraud_amount': fraud_amount,
            'fraud_percentage': fraud_percentage,
            'avg_transaction_amount': avg_amount,
            'avg_fraud_amount': avg_fraud_amount,
            'merchant_categories': merchant_categories,
            'locations': locations
        }
        
        logger.info("Fraud statistics calculated successfully")
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating fraud statistics: {str(e)}")
        raise

def get_time_series_data(transactions, interval='day'):
    """
    Get time series data for fraud analysis
    
    Parameters:
    -----------
    transactions : list
        List of Transaction objects
    interval : str
        Time interval for grouping ('hour', 'day', 'week', 'month')
    
    Returns:
    --------
    dict
        Dictionary with time series data
    """
    try:
        logger.info(f"Generating time series data with interval: {interval}")
        
        # Convert transactions to DataFrame for easier manipulation
        df = pd.DataFrame([
            {
                'timestamp': t.timestamp,
                'amount': t.amount,
                'is_fraud': t.is_fraud
            }
            for t in transactions
        ])
        
        if df.empty:
            return {'labels': [], 'total_counts': [], 'fraud_counts': [], 'fraud_amounts': []}
        
        # Set the timestamp as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Group by time interval
        if interval == 'hour':
            df['time_group'] = df['timestamp'].dt.floor('H')
        elif interval == 'day':
            df['time_group'] = df['timestamp'].dt.floor('D')
        elif interval == 'week':
            df['time_group'] = df['timestamp'].dt.floor('W')
        elif interval == 'month':
            df['time_group'] = df['timestamp'].dt.floor('M')
        else:
            raise ValueError(f"Invalid interval: {interval}")
        
        # Create aggregations
        agg_data = df.groupby('time_group').agg(
            total_count=('timestamp', 'count'),
            fraud_count=('is_fraud', 'sum'),
            total_amount=('amount', 'sum'),
            fraud_amount=('amount', lambda x: sum(x[df.loc[x.index, 'is_fraud']]))
        ).reset_index()
        
        # Format time labels
        if interval == 'hour':
            time_format = '%Y-%m-%d %H:00'
        elif interval == 'day':
            time_format = '%Y-%m-%d'
        elif interval == 'week':
            time_format = '%Y-%m-%d'
        else:  # month
            time_format = '%Y-%m'
        
        # Prepare the result
        result = {
            'labels': agg_data['time_group'].dt.strftime(time_format).tolist(),
            'total_counts': agg_data['total_count'].tolist(),
            'fraud_counts': agg_data['fraud_count'].tolist(),
            'total_amounts': agg_data['total_amount'].tolist(),
            'fraud_amounts': agg_data['fraud_amount'].tolist()
        }
        
        logger.info("Time series data generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating time series data: {str(e)}")
        raise
