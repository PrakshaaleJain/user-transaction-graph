from faker import Faker
import random
import uuid
from tqdm import tqdm
from .database import db

fake = Faker()

def seed_data(num_users=50, num_txns=100000):
    print(f"Generating {num_users} users...")
    users = []

    for _ in range(num_users):
        user = {
            "user_id": str(uuid.uuid4())[:8],
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "address": fake.address(),
            "payment_method": random.choice(["visa", "paypal", "bank", "mastercard"])
        }
        users.append(user)

        db.query("""
        MERGE (u:User {user_id: $user_id})
        SET u.name = $name, u.email = $email, u.phone = $phone,
            u.address = $address, u.payment_method = $payment_method
        """, user)

    print("Users created successfully.")
    print(f"Generating {num_txns} transactions...")
    for _ in tqdm(range(num_txns)):
        sender, receiver = random.sample(users, 2)
        txn = {
            "txn_id": str(uuid.uuid4())[:8],
            "sender_id": sender["user_id"],
            "receiver_id": receiver["user_id"],
            "amount": round(random.uniform(5, 5000), 2),
            "device_id": random.choice(["d1", "d2", "d3", "d4", "d5"]),
            "ip_address": random.choice([
                "192.168.0.10", "192.168.0.20",
                "10.0.0.1", "10.0.0.2", "172.16.0.5"
            ])
        }

        db.query("""
        MERGE (t:Transaction {txn_id: $txn_id})
        SET t.amount = $amount, t.device_id = $device_id, t.ip_address = $ip_address
        WITH t
        MATCH (s:User {user_id: $sender_id}), (r:User {user_id: $receiver_id})
        MERGE (s)-[:SENT]->(t)
        MERGE (t)-[:RECEIVED_BY]->(r)
        """, txn)

    print("Transactions created successfully.")
    print("✅ Database seeding complete!")


if __name__ == "__main__":
    seed_data(num_users=10, num_txns=100000)
