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

    # Customer phone, format +233XXXXXXXXX (9 digits after country code), random per row
    phone_numbers = np.random.randint(100000000, 1000000000, size=2000)
    customer_phones = [f"+233{num}" for num in phone_numbers]

    # Amount: Float, GHS 20.00–2000.00, 2 decimal places
    amounts = np.round(np.random.uniform(20.00, 2000.00, size=2000), 2)

    # Timestamp: Random datetimes spanning the last 6 months from script run date
    run_date = datetime.now()
    total_seconds = 180 * 24 * 60 * 60  # 6 months in seconds
    random_offsets = np.random.randint(0, total_seconds, size=2000)
    timestamps = [run_date - timedelta(seconds=int(offset)) for offset in random_offsets]

    # Payment method: cash / momo / bank_transfer, weighted 50% / 35% / 15%
    payment_methods = np.random.choice(
        ['cash', 'momo', 'bank_transfer'], 
        size=2000, 
        p=[0.50, 0.35, 0.15]
    )

    # Remittance status: remitted / pending / missed, weighted 70% / 15% / 15%
    remittance_statuses = np.random.choice(
        ['remitted', 'pending', 'missed'], 
        size=2000, 
        p=[0.70, 0.15, 0.15]
    )

    # Branch: Accra / Kumasi / Tamale / Takoradi / Cape_Coast, random per row
    branches = np.random.choice(
        ['Accra', 'Kumasi', 'Tamale', 'Takoradi', 'Cape_Coast'], 
        size=2000
    )

    # Customer call language_pref: english / twi / dagbani (40% / 35% / 25%)
    language_prefs = np.random.choice(
        ['english', 'twi', 'dagbani'],
        size=2000,
        p=[0.40, 0.35, 0.25]
    )

    # Assemble base DataFrame
    df = pd.DataFrame({
        'agent_id': agent_ids,
        'customer_id': customer_ids,
        'customer_phone': customer_phones,
        'amount': amounts,
        'timestamp': pd.to_datetime(timestamps),
        'payment_method': payment_methods,
        'remittance_status': remittance_statuses,
        'branch': branches,
        'language_pref': language_prefs
    })

    # Output paths (using pathlib.Path(__file__).parent for dynamic resolution)
    script_dir = Path(__file__).parent.resolve()
    base_csv_path = script_dir / "agent_transactions.csv"
    features_csv_path = script_dir / "agent_transactions_features.csv"

    # Save agent_transactions.csv (format timestamp to YYYY-MM-DD HH:MM:SS)
    df_base_to_save = df.copy()
    df_base_to_save['timestamp'] = df_base_to_save['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_base_to_save.to_csv(base_csv_path, index=False)

    # 2. Engineer features -> agent_transactions_features.csv
    # Feature A: remittance_delay_hours (0 if remitted, else random int 24-720 inclusive)
    mask_not_remitted = df['remittance_status'] != 'remitted'
    num_not_remitted = mask_not_remitted.sum()
    delays = np.zeros(len(df), dtype=int)
    # np.random.randint is high-exclusive, so we use 721 to include 720
    delays[mask_not_remitted] = np.random.randint(24, 721, size=num_not_remitted)
    df['remittance_delay_hours'] = delays

    # Feature B: cash_ratio
    # Per agent_id, proportion of that agent's rows where payment_method == 'cash', round to 4 dp
    agent_cash_count = df[df['payment_method'] == 'cash'].groupby('agent_id').size()
    agent_total_count = df.groupby('agent_id').size()
    cash_ratio = (agent_cash_count / agent_total_count).fillna(0.0).round(4)
    df['cash_ratio'] = df['agent_id'].map(cash_ratio)

    # Feature C: deviation_from_agent_mean
    # Amount minus that agent's mean amount (round to 2 dp)
    agent_mean_amount = df.groupby('agent_id')['amount'].transform('mean')
    df['deviation_from_agent_mean'] = (df['amount'] - agent_mean_amount).round(2)

    # Feature D: missed_consecutive_count
    # Per agent_id, sorted by timestamp ascending — running streak of consecutive missed rows, resetting to 0 on any non-missed row
    df['original_index'] = df.index
    df_sorted = df.sort_values(by=['agent_id', 'timestamp']).copy()
    
    def calculate_streak(group):
        streak = []
        current = 0
        for status in group['remittance_status']:
            if status == 'missed':
                current += 1
            else:
                current = 0
            streak.append(current)
        return pd.Series(streak, index=group.index)
        
    df_sorted['missed_consecutive_count'] = df_sorted.groupby('agent_id', group_keys=False).apply(calculate_streak)
    df = df_sorted.sort_values(by='original_index').drop(columns=['original_index'])

    # Feature E: is_fraud
    # 1 if remittance_delay_hours > 168 AND cash_ratio > 0.6, else 0
    df['is_fraud'] = ((df['remittance_delay_hours'] > 168) & (df['cash_ratio'] > 0.6)).astype(int)

    # Save agent_transactions_features.csv (format timestamp to YYYY-MM-DD HH:MM:SS)
    df_features_to_save = df.copy()
    df_features_to_save['timestamp'] = df_features_to_save['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_features_to_save.to_csv(features_csv_path, index=False)

    # 3. Print summary to stdout
    total_rows = len(df)
    fraud_cases = df['is_fraud'].sum()
    fraud_percentage = (fraud_cases / total_rows) * 100

    print(f"Total rows: {total_rows}")
    print(f"Fraud cases: {fraud_cases}")
    print(f"Fraud percentage: {fraud_percentage:.2f}%")
    print("\nFraud by Branch:")
    
    branch_fraud = df.groupby('branch')['is_fraud'].sum()
    for br in sorted(['Accra', 'Cape_Coast', 'Kumasi', 'Takoradi', 'Tamale']):
        count = branch_fraud.get(br, 0)
        print(f"  {br:<13}: {count}")

if __name__ == "__main__":
    generate_synthetic_data()
