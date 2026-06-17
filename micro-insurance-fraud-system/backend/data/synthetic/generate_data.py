import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

def generate_synthetic_data():
    # Set numpy random seed to 42 for reproducibility
    np.random.seed(42)

    # 1. Generate agent_transactions.csv
    # 50 unique agents, format AGT001–AGT050
    agents = [f"AGT{i:03d}" for i in range(1, 51)]
    agent_ids = np.random.choice(agents, size=2000)

    # Customers, format CUST0001–CUST0500
    customers = [f"CUST{i:04d}" for i in range(1, 501)]
    customer_ids = np.random.choice(customers, size=2000)

    # Amount: Float, GHS 20.00–2000.00, 2 decimal places
    amounts = np.round(np.random.uniform(20.00, 2000.00, size=2000), 2)

    # Timestamp: Random datetimes spanning the last 6 months from script run date
    run_date = datetime.now()
    total_seconds = 180 * 24 * 60 * 60  # 6 months in seconds
    random_offsets = np.random.randint(0, total_seconds, size=2000)
    timestamps = [run_date - timedelta(seconds=int(offset)) for offset in random_offsets]

    # Payment method: One of: cash, momo, bank_transfer; uniform random
    payment_methods = np.random.choice(['cash', 'momo', 'bank_transfer'], size=2000)

    # Remittance status: One of: remitted, pending, missed; weighted 70% / 15% / 15%
    remittance_statuses = np.random.choice(
        ['remitted', 'pending', 'missed'], 
        size=2000, 
        p=[0.70, 0.15, 0.15]
    )

    # Branch: One of: Accra, Kumasi, Tamale, Takoradi, Cape_Coast; random per row
    branches = np.random.choice(
        ['Accra', 'Kumasi', 'Tamale', 'Takoradi', 'Cape_Coast'], 
        size=2000
    )

    # Assemble base DataFrame
    df = pd.DataFrame({
        'agent_id': agent_ids,
        'customer_id': customer_ids,
        'amount': amounts,
        'timestamp': pd.to_datetime(timestamps),
        'payment_method': payment_methods,
        'remittance_status': remittance_statuses,
        'branch': branches
    })

    # Output paths
    script_dir = Path(__file__).parent.resolve()
    base_csv_path = script_dir / "agent_transactions.csv"
    features_csv_path = script_dir / "agent_transactions_features.csv"

    # Save agent_transactions.csv (convert timestamps to string format YYYY-MM-DD HH:MM:SS)
    df_base_to_save = df.copy()
    df_base_to_save['timestamp'] = df_base_to_save['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_base_to_save.to_csv(base_csv_path, index=False)

    # 2. Engineer features -> agent_transactions_features.csv
    # Feature A: remittance_delay_hours
    # If missed/pending: random int [24, 720] inclusive. If remitted: 0
    mask_pending_missed = df['remittance_status'].isin(['pending', 'missed'])
    num_pending_missed = mask_pending_missed.sum()
    delays = np.zeros(len(df), dtype=int)
    delays[mask_pending_missed] = np.random.randint(24, 721, size=num_pending_missed)
    df['remittance_delay_hours'] = delays

    # Feature B: cash_ratio
    # Per agent_id: proportion of cash payment method, mapped back, rounded to 4 decimals
    agent_cash_count = df[df['payment_method'] == 'cash'].groupby('agent_id').size()
    agent_total_count = df.groupby('agent_id').size()
    cash_ratio = (agent_cash_count / agent_total_count).fillna(0.0).round(4)
    df['cash_ratio'] = df['agent_id'].map(cash_ratio)

    # Feature C: deviation_from_agent_mean
    # Amount minus that agent's mean amount, rounded to 2 decimals
    agent_mean_amount = df.groupby('agent_id')['amount'].transform('mean')
    df['deviation_from_agent_mean'] = (df['amount'] - agent_mean_amount).round(2)

    # Feature D: missed_consecutive_count
    # Sort by agent_id and timestamp ascending to count consecutive missed streak
    df_sorted = df.sort_values(by=['agent_id', 'timestamp'])
    is_missed = (df_sorted['remittance_status'] == 'missed').astype(int)
    # block increments every time status is NOT 'missed', creating sub-groups for cumsum
    block = (df_sorted['remittance_status'] != 'missed').groupby(df_sorted['agent_id']).cumsum()
    df_sorted['missed_consecutive_count'] = is_missed.groupby([df_sorted['agent_id'], block]).cumsum()
    
    # Assign back to original order dataframe via index alignment
    df['missed_consecutive_count'] = df_sorted['missed_consecutive_count']

    # Feature E: is_fraud
    # 1 if remittance_delay_hours > 168 AND cash_ratio > 0.6, else 0
    df['is_fraud'] = ((df['remittance_delay_hours'] > 168) & (df['cash_ratio'] > 0.6)).astype(int)

    # Save agent_transactions_features.csv (convert timestamps to string format YYYY-MM-DD HH:MM:SS)
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df.to_csv(features_csv_path, index=False)

    # 3. Print summary to stdout
    total_rows = len(df)
    fraud_cases = df['is_fraud'].sum()
    fraud_percentage = (fraud_cases / total_rows) * 100

    print("=== Fraud Detection Summary ===")
    print(f"Total rows: {total_rows}")
    print(f"Fraud cases: {fraud_cases}")
    print(f"Fraud percentage: {fraud_percentage:.2f}%")
    print("\nFraud by Branch:")
    
    # Sort branches to keep list ordered consistently
    branch_fraud = df.groupby('branch')['is_fraud'].sum()
    for br in sorted(['Accra', 'Cape_Coast', 'Kumasi', 'Takoradi', 'Tamale']):
        count = branch_fraud.get(br, 0)
        print(f"  {br:<14}: {count}")

if __name__ == "__main__":
    generate_synthetic_data()
