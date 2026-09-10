"""Synthetic Transaction Dataset Generator.

Generates realistic normal financial transactions along with 5 distinct anomaly types:
- HIGH_AMOUNT_SPIKE: Unusually high spending spikes compared to user baseline
- RAPID_BURST: High velocity transaction frequency bursts in small time windows
- LOCATION_HOPPING: Geographic anomalies originating from unfamiliar/foreign locations
- UNRECOGNIZED_DEVICE: Transactions initiated via emulators or unrecognized devices
- FAILED_ATTEMPT_STUFFING: Repeated failed/rejected attempts before transaction
"""

import argparse
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd

MERCHANTS_BY_CATEGORY = {
    "Shopping": ["Amazon India", "Flipkart", "Myntra", "Zara", "H&M", "Ajio"],
    "Food & Dining": ["Swiggy", "Zomato", "Starbucks", "McDonald's", "Dominos", "Barbeque Nation"],
    "Groceries": ["Blinkit", "Zepto", "Instamart", "BigBasket", "DMart", "Nature's Basket"],
    "Travel": ["Uber", "Ola", "MakeMyTrip", "IRCTC", "IndiGo", "Booking.com"],
    "Electronics": ["Apple Store", "Croma", "Reliance Digital", "Samsung Store", "Vijay Sales"],
    "Entertainment": ["BookMyShow", "Netflix", "Spotify", "PVR Cinemas", "Steam Games"],
    "Utilities": ["Tata Power", "Airtel Bill", "Jio Recharge", "Adani Gas", "Bescom"],
    "Luxury & Jewelry": ["Tanishq", "Malabar Gold", "Rolex Boutique", "Tiffany & Co", "CaratLane"],
}

NORMAL_LOCATIONS = [
    "Mumbai, IN",
    "Bengaluru, IN",
    "Delhi, IN",
    "Hyderabad, IN",
    "Pune, IN",
    "Chennai, IN",
    "Kolkata, IN",
    "Ahmedabad, IN",
]

ANOMALOUS_LOCATIONS = [
    "Lagos, NG",
    "Moscow, RU",
    "Dubai, AE",
    "London, UK",
    "Singapore, SG",
    "Cayman Islands, KY",
    "Bucharest, RO",
]


def generate_synthetic_transactions(
    num_transactions: int = 5000,
    num_users: int = 50,
    anomaly_ratio: float = 0.06,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Generate a realistic dataset of financial transactions with labeled normal/fraud patterns."""
    random.seed(random_seed)
    np.random.seed(random_seed)

    print(
        f"Generating {num_transactions} synthetic transactions across {num_users} users "
        f"(anomaly_ratio={anomaly_ratio}, seed={random_seed})..."
    )

    # Build user profiles with regular device and home location
    users = []
    for uid in range(1, num_users + 1):
        users.append(
            {
                "user_id": uid,
                "home_location": random.choice(NORMAL_LOCATIONS),
                "primary_device": f"device-mobile-{uid:03d}",
                "secondary_device": f"device-laptop-{uid:03d}" if random.random() > 0.4 else None,
                "avg_spend": float(np.random.uniform(500, 3500)),
            }
        )

    records: List[Dict[str, Any]] = []
    base_time = datetime.now(timezone.utc) - timedelta(days=30)

    # 1. Generate normal transactions
    num_normal = int(num_transactions * (1 - anomaly_ratio))
    for _ in range(num_normal):
        user = random.choice(users)
        category = random.choice(list(MERCHANTS_BY_CATEGORY.keys()))
        if category == "Luxury & Jewelry" and random.random() > 0.15:
            category = "Shopping"

        merchant = random.choice(MERCHANTS_BY_CATEGORY[category])

        # Lognormal amount distribution around user average
        amount = float(np.random.lognormal(mean=np.log(user["avg_spend"]), sigma=0.5))
        amount = round(min(45000.0, max(50.0, amount)), 2)

        # Device: 85% primary, 15% secondary if present
        if user["secondary_device"] and random.random() > 0.8:
            device_id = user["secondary_device"]
        else:
            device_id = user["primary_device"]

        # Location: 90% home location, 10% other normal city
        if random.random() > 0.9:
            location = random.choice(NORMAL_LOCATIONS)
        else:
            location = user["home_location"]

        # Random timestamp over last 30 days
        seconds_offset = random.randint(0, 30 * 24 * 3600)
        tx_time = base_time + timedelta(seconds=seconds_offset)

        records.append(
            {
                "transaction_id": str(uuid.uuid4()),
                "user_id": user["user_id"],
                "amount": amount,
                "merchant": merchant,
                "category": category,
                "location": location,
                "device_id": device_id,
                "timestamp": tx_time.isoformat(),
                "status": "APPROVED",
                "is_anomaly": 0,
                "anomaly_type": "None",
            }
        )

    # 2. Generate anomalous transactions
    num_anomalies = num_transactions - num_normal
    anomaly_types = [
        "HIGH_AMOUNT_SPIKE",
        "RAPID_BURST",
        "LOCATION_HOPPING",
        "UNRECOGNIZED_DEVICE",
        "FAILED_ATTEMPT_STUFFING",
    ]

    for _ in range(num_anomalies):
        user = random.choice(users)
        atype = random.choice(anomaly_types)
        seconds_offset = random.randint(0, 30 * 24 * 3600)
        tx_time = base_time + timedelta(seconds=seconds_offset)

        if atype == "HIGH_AMOUNT_SPIKE":
            category = random.choice(["Luxury & Jewelry", "Electronics"])
            merchant = random.choice(MERCHANTS_BY_CATEGORY[category])
            amount = round(float(np.random.uniform(60000, 350000)), 2)
            location = user["home_location"]
            device_id = user["primary_device"]
            status_val = "FLAGGED"

        elif atype == "RAPID_BURST":
            category = "Shopping"
            merchant = "Amazon India"
            amount = round(float(np.random.uniform(5000, 25000)), 2)
            location = user["home_location"]
            device_id = user["primary_device"]
            status_val = "SUSPICIOUS"

        elif atype == "LOCATION_HOPPING":
            category = random.choice(["Travel", "Shopping"])
            merchant = random.choice(MERCHANTS_BY_CATEGORY[category])
            amount = round(float(np.random.uniform(2000, 40000)), 2)
            location = random.choice(ANOMALOUS_LOCATIONS)
            device_id = user["primary_device"]
            status_val = "SUSPICIOUS"

        elif atype == "UNRECOGNIZED_DEVICE":
            category = "Electronics"
            merchant = "Apple Store"
            amount = round(float(np.random.uniform(15000, 95000)), 2)
            location = random.choice(NORMAL_LOCATIONS)
            device_id = f"device-emulator-root-{random.randint(1000, 9999)}"
            status_val = "SUSPICIOUS"

        else:  # FAILED_ATTEMPT_STUFFING
            category = "Shopping"
            merchant = "Steam Games"
            amount = round(float(np.random.uniform(1000, 8000)), 2)
            location = random.choice(ANOMALOUS_LOCATIONS)
            device_id = f"device-botnet-{random.randint(10, 99)}"
            status_val = "FLAGGED"

        records.append(
            {
                "transaction_id": str(uuid.uuid4()),
                "user_id": user["user_id"],
                "amount": amount,
                "merchant": merchant,
                "category": category,
                "location": location,
                "device_id": device_id,
                "timestamp": tx_time.isoformat(),
                "status": status_val,
                "is_anomaly": 1,
                "anomaly_type": atype,
            }
        )

    df = pd.DataFrame(records)
    # Sort chronologically
    df["dt"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("dt").drop(columns=["dt"]).reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic transaction dataset for FinTrack."
    )
    parser.add_argument(
        "--rows", type=int, default=5000, help="Total number of transactions (default: 5000)"
    )
    parser.add_argument(
        "--users", type=int, default=50, help="Number of simulated users (default: 50)"
    )
    parser.add_argument(
        "--anomaly-ratio",
        type=float,
        default=0.06,
        help="Fraction of anomalous transactions (default: 0.06)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(
            os.path.dirname(__file__), "..", "data", "synthetic", "transactions.csv"
        ),
        help="Path to output CSV file",
    )

    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    df = generate_synthetic_transactions(
        num_transactions=args.rows,
        num_users=args.users,
        anomaly_ratio=args.anomaly_ratio,
        random_seed=args.seed,
    )
    df.to_csv(args.output, index=False)
    print(f"\nGenerated {len(df)} transactions saved to: {args.output}")
    print("\nAnomaly Distribution:")
    print(df["anomaly_type"].value_counts())


if __name__ == "__main__":
    main()
