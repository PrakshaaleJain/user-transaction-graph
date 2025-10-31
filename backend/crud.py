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

def get_users():
    """Get all users for the API"""
    result = db.query("MATCH (u:User) RETURN u")
    return [dict(record["u"]) for record in result]

def get_transactions():
    """Get all transactions for the API"""
    result = db.query("MATCH (t:Transaction) RETURN t")
    return [dict(record["t"]) for record in result]

def get_graph_data():
    """Get all users, transactions and their relationships for visualization"""
    query = """
    MATCH (u:User)
    OPTIONAL MATCH (u)-[:SENT]->(t:Transaction)
    OPTIONAL MATCH (t)-[:RECEIVED_BY]->(r:User)
    OPTIONAL MATCH (u)-[:SHARED_ATTRIBUTE]->(su:User)
    OPTIONAL MATCH (t)-[:LINKED]->(lt:Transaction)
    RETURN u, t, r, su, lt
    """
    result = db.query(query)
    
    nodes = []
    edges = []
    node_ids = set()
    
    for record in result:
        # Add user nodes
        if record["u"] and record["u"]["user_id"] not in node_ids:
            user_data = dict(record["u"])
            nodes.append({
                "data": {
                    "id": user_data["user_id"],
                    "label": user_data.get("name", user_data["user_id"]),
                    "type": "user",
                    **user_data
                }
            })
            node_ids.add(user_data["user_id"])
        
        # Add receiver user nodes
        if record["r"] and record["r"]["user_id"] not in node_ids:
            user_data = dict(record["r"])
            nodes.append({
                "data": {
                    "id": user_data["user_id"],
                    "label": user_data.get("name", user_data["user_id"]),
                    "type": "user",
                    **user_data
                }
            })
            node_ids.add(user_data["user_id"])
        
        # Add shared attribute user nodes
        if record["su"] and record["su"]["user_id"] not in node_ids:
            user_data = dict(record["su"])
            nodes.append({
                "data": {
                    "id": user_data["user_id"],
                    "label": user_data.get("name", user_data["user_id"]),
                    "type": "user",
                    **user_data
                }
            })
            node_ids.add(user_data["user_id"])
        
        # Add transaction nodes
        if record["t"] and record["t"]["txn_id"] not in node_ids:
            txn_data = dict(record["t"])
            nodes.append({
                "data": {
                    "id": txn_data["txn_id"],
                    "label": f"${txn_data.get('amount', 0)}",
                    "type": "transaction",
                    **txn_data
                }
            })
            node_ids.add(txn_data["txn_id"])
        
        # Add linked transaction nodes
        if record["lt"] and record["lt"]["txn_id"] not in node_ids:
            txn_data = dict(record["lt"])
            nodes.append({
                "data": {
                    "id": txn_data["txn_id"],
                    "label": f"${txn_data.get('amount', 0)}",
                    "type": "transaction",
                    **txn_data
                }
            })
            node_ids.add(txn_data["txn_id"])
        
        # Add edges
        if record["u"] and record["t"]:
            edges.append({
                "data": {
                    "id": f"{record['u']['user_id']}-sent-{record['t']['txn_id']}",
                    "source": record["u"]["user_id"],
                    "target": record["t"]["txn_id"],
                    "type": "SENT"
                }
            })
        
        if record["t"] and record["r"]:
            edges.append({
                "data": {
                    "id": f"{record['t']['txn_id']}-received-{record['r']['user_id']}",
                    "source": record["t"]["txn_id"],
                    "target": record["r"]["user_id"],
                    "type": "RECEIVED_BY"
                }
            })
        
        if record["u"] and record["su"]:
            edges.append({
                "data": {
                    "id": f"{record['u']['user_id']}-shared-{record['su']['user_id']}",
                    "source": record["u"]["user_id"],
                    "target": record["su"]["user_id"],
                    "type": "SHARED_ATTRIBUTE"
                }
            })
        
        if record["t"] and record["lt"]:
            edges.append({
                "data": {
                    "id": f"{record['t']['txn_id']}-linked-{record['lt']['txn_id']}",
                    "source": record["t"]["txn_id"],
                    "target": record["lt"]["txn_id"],
                    "type": "LINKED"
                }
            })
    
    return {"nodes": nodes, "edges": edges}

def get_user_transactions(user_id):
    """Get all transactions for a specific user"""
    query = """
    MATCH (u:User {user_id: $user_id})
    OPTIONAL MATCH (u)-[:SENT]->(t:Transaction)-[:RECEIVED_BY]->(r:User)
    RETURN u, t, r
    """
    result = db.query(query, {"user_id": user_id})
    return [{
        "user": dict(record["u"]) if record["u"] else None,
        "transaction": dict(record["t"]) if record["t"] else None,
        "receiver": dict(record["r"]) if record["r"] else None
    } for record in result]

def get_transaction_details(txn_id):
    """Get details of a specific transaction"""
    query = """
    MATCH (s:User)-[:SENT]->(t:Transaction {txn_id: $txn_id})-[:RECEIVED_BY]->(r:User)
    RETURN s, t, r
    """
    result = db.query(query, {"txn_id": txn_id})
    return [{
        "sender": dict(record["s"]) if record["s"] else None,
        "transaction": dict(record["t"]) if record["t"] else None,
        "receiver": dict(record["r"]) if record["r"] else None
    } for record in result]

def load_sample_data():
    """Load sample data into the database"""
    # Clear existing data
    db.query("MATCH (n) DETACH DELETE n")
    
    # Create sample users
    users = [
        {"user_id": "user1", "name": "Alice Johnson", "email": "alice@email.com", "phone": "555-0101", "address": "123 Main St", "payment_method": "credit_card"},
        {"user_id": "user2", "name": "Bob Smith", "email": "bob@email.com", "phone": "555-0102", "address": "456 Oak Ave", "payment_method": "paypal"},
        {"user_id": "user3", "name": "Charlie Brown", "email": "charlie@email.com", "phone": "555-0103", "address": "789 Pine Rd", "payment_method": "credit_card"},
        {"user_id": "user4", "name": "Diana Prince", "email": "diana@email.com", "phone": "555-0104", "address": "123 Main St", "payment_method": "bank_transfer"},
        {"user_id": "user5", "name": "Eve Adams", "email": "eve@email.com", "phone": "555-0105", "address": "321 Elm St", "payment_method": "paypal"}
    ]
    
    for user in users:
        create_user(user)
    
    # Create sample transactions
    transactions = [
        {"txn_id": "txn1", "sender_id": "user1", "receiver_id": "user2", "amount": 100.50, "device_id": "device_001", "ip_address": "192.168.1.100"},
        {"txn_id": "txn2", "sender_id": "user2", "receiver_id": "user3", "amount": 250.75, "device_id": "device_002", "ip_address": "192.168.1.101"},
        {"txn_id": "txn3", "sender_id": "user3", "receiver_id": "user4", "amount": 75.25, "device_id": "device_001", "ip_address": "192.168.1.102"},
        {"txn_id": "txn4", "sender_id": "user4", "receiver_id": "user5", "amount": 300.00, "device_id": "device_003", "ip_address": "192.168.1.100"},
        {"txn_id": "txn5", "sender_id": "user5", "receiver_id": "user1", "amount": 150.30, "device_id": "device_002", "ip_address": "192.168.1.103"}
    ]
    
    for txn in transactions:
        create_transaction(txn)
    
    return True
