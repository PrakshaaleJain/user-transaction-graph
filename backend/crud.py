from .database import db

def create_user(user_data):
    query = """
    MERGE (u:User {user_id: $user_id})
    SET u.name = $name,
        u.email = $email,
        u.phone = $phone,
        u.address = $address,
        u.payment_method = $payment_method
    RETURN u
    """
    db.query(query, user_data)

    # Detect and create shared attribute relationships
    detect_user_relationships(user_data["user_id"])

def create_transaction(txn_data):
    # Create the transaction node
    query = """
    MERGE (t:Transaction {txn_id: $txn_id})
    SET t.amount = $amount,
        t.device_id = $device_id,
        t.ip_address = $ip_address
    WITH t
    MATCH (s:User {user_id: $sender_id}), (r:User {user_id: $receiver_id})
    MERGE (s)-[:SENT]->(t)
    MERGE (t)-[:RECEIVED_BY]->(r)
    RETURN t
    """
    db.query(query, txn_data)

    # Detect transaction-to-transaction links
    detect_transaction_relationships(txn_data["txn_id"])

def get_all_users(limit: int = 200):
    return db.query("MATCH (u:User) RETURN u LIMIT $limit", {"limit": limit})

def get_all_transactions(limit: int = 200):
    return db.query("MATCH (t:Transaction) RETURN t LIMIT $limit", {"limit": limit})


def detect_user_relationships(user_id):
    """Find users with shared attributes and create edges."""
    query = """
    MATCH (u1:User {user_id: $user_id}), (u2:User)
    WHERE u1 <> u2
      AND (
        (u1.email IS NOT NULL AND u1.email = u2.email) OR
        (u1.phone IS NOT NULL AND u1.phone = u2.phone) OR
        (u1.address IS NOT NULL AND u1.address = u2.address) OR
        (u1.payment_method IS NOT NULL AND u1.payment_method = u2.payment_method)
      )
    MERGE (u1)-[:SHARED_ATTRIBUTE]->(u2)
    """
    db.query(query, {"user_id": user_id})

def detect_transaction_relationships(txn_id):
    """Link transactions that share same device or IP."""
    query = """
    MATCH (t1:Transaction {txn_id: $txn_id}), (t2:Transaction)
    WHERE t1 <> t2
      AND (
        (t1.device_id IS NOT NULL AND t1.device_id = t2.device_id) OR
        (t1.ip_address IS NOT NULL AND t1.ip_address = t2.ip_address)
      )
    MERGE (t1)-[:LINKED]->(t2)
    """
    db.query(query, {"txn_id": txn_id})
