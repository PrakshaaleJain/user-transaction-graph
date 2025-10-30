from .database import db

def get_user_relationships(user_id: str):
    query = """
    MATCH (u:User {user_id: $user_id})-[r]-(connected)
    RETURN type(r) as relation, connected
    """
    return db.query(query, {"user_id": user_id})

def get_transaction_relationships(txn_id: str):
    query = """
    MATCH (t:Transaction {txn_id: $txn_id})-[r]-(connected)
    RETURN type(r) as relation, connected
    """
    return db.query(query, {"txn_id": txn_id})
