import os
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from backend.app.db import SessionLocal
from backend.app.models.agent import Agent
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.alert import FraudAlert
from backend.app.ml.fraud_detection import score_transaction

logger = logging.getLogger(__name__)

async def seed_if_empty():
    """
    Checks if agents and transactions tables are empty.
    If so, seeds them with the synthetic dataset and scores each row using the ML models.
    Also ensures fraud_alerts is populated with PENDING alerts for high-risk agents.
    """
    db = SessionLocal()
    try:
        agent_count = db.query(Agent).count()
        tx_count = db.query(Transaction).count()
        
        # Only seed agents and transactions if empty
        if agent_count == 0 and tx_count == 0:
            # Resolve path to synthetic CSV file
            base_dir = Path(__file__).resolve().parent.parent.parent
            csv_path = base_dir / "data" / "synthetic" / "agent_transactions_features.csv"
            
            if not csv_path.exists():
                logger.error(f"Seed CSV file not found at: {csv_path}")
            else:
                logger.info("Starting one-time database seeding from CSV features dataset...")
                df = pd.read_csv(csv_path)
                if not df.empty:
                    # 1. Insert unique agents first
                    unique_agents = df.drop_duplicates(subset=['agent_id'])[['agent_id', 'branch']]
                    logger.info(f"Inserting {len(unique_agents)} unique agents...")
                    
                    for _, row in unique_agents.iterrows():
                        aid = str(row['agent_id'])
                        branch = str(row['branch'])
                        agent = Agent(
                            agent_id=aid,
                            full_name=f"Agent {aid}",
                            branch=branch,
                            phone=None
                        )
                        db.add(agent)
                    
                    # Flush to DB to resolve unique agent constraints before inserting transactions
                    db.flush()

                    # 2. Insert all transactions and compute features
                    logger.info(f"Scoring and inserting {len(df)} transactions and features...")
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    for idx, row in df.iterrows():
                        aid = str(row['agent_id'])
                        timestamp_dt = row['timestamp'].to_pydatetime()
                        
                        # Create transaction row
                        tx = Transaction(
                            agent_id=aid,
                            customer_id=str(row['customer_id']),
                            customer_phone=str(row['customer_phone']) if not pd.isna(row['customer_phone']) else None,
                            amount=float(row['amount']),
                            timestamp=timestamp_dt,
                            payment_method=str(row['payment_method']),
                            remittance_status=str(row['remittance_status']),
                            branch=str(row['branch'])
                        )
                        db.add(tx)
                        db.flush()  # Resolve transaction ID for foreign key reference
                        
                        # Pre-calculate machine learning features for transaction_features
                        feature_dict = {
                            'remittance_delay_hours': int(row['remittance_delay_hours']),
                            'cash_ratio': float(row['cash_ratio']),
                            'deviation_from_agent_mean': float(row['deviation_from_agent_mean']),
                            'missed_consecutive_count': int(row['missed_consecutive_count']),
                            'amount': float(row['amount'])
                        }
                        
                        # Compute risk scores
                        scored = score_transaction(feature_dict)
                        
                        # Create feature row
                        feat = TransactionFeature(
                            transaction_id=tx.id,
                            remittance_delay_hours=int(row['remittance_delay_hours']),
                            cash_ratio=float(row['cash_ratio']),
                            deviation_from_agent_mean=float(row['deviation_from_agent_mean']),
                            missed_consecutive_count=int(row['missed_consecutive_count']),
                            is_fraud=bool(scored['is_fraud']),
                            risk_score=float(scored['risk_score']),
                            flag_reason=str(scored['flag_reason']),
                            scored_at=timestamp_dt
                        )
                        db.add(feat)
                        
                        # Commit periodically to keep transactions optimized
                        if idx % 200 == 0:
                            db.flush()

                    db.commit()
                    logger.info("Database seeding and machine learning pre-scoring finished successfully!")

        # 3. Ensure fraud_alerts table has PENDING alerts for high-risk agents (>= 70%) if empty
        alert_count = db.query(FraudAlert).count()
        if alert_count == 0:
            logger.info("Fraud alerts table is empty. Seeding PENDING alerts for high-risk agents...")
            from backend.app.routes.agents import compute_all_agent_risk_scores
            agent_scores = compute_all_agent_risk_scores(db)

            seeded_alerts = 0
            for agent in agent_scores:
                aid = agent["agent_id"]
                risk_score = agent["risk_score"]
                if risk_score >= 70.0:
                    alert_obj = FraudAlert(
                        agent_id=aid,
                        transaction_id=agent.get("latest_tx_id"),
                        risk_score=risk_score,
                        flag_reason=agent["flag_reason"],
                        branch=agent["branch"],
                        status="PENDING",
                        alerted_at=datetime.utcnow(),
                        acknowledged=False
                    )
                    db.add(alert_obj)
                    seeded_alerts += 1

            db.commit()
            logger.info(f"Seeded {seeded_alerts} PENDING fraud alerts into database.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {str(e)}")
        raise e
    finally:
        db.close()
