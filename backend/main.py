from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import User, Transaction
from . import crud
from .database import db
import os
import io
import csv

app = FastAPI(title="User & Transaction Graph API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/users")
def add_user(user: User):
    crud.create_user(user.dict())
    return {"message": f"User {user.user_id} added or updated."}

@app.post("/transactions")
def add_transaction(txn: Transaction):
    try:
        result = crud.create_transaction(txn.dict())
        return {"message": f"Transaction {txn.txn_id} added successfully.", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
def list_users():
    try:
        users = crud.get_all_users()
        return [record.get("u", record) for record in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transactions")
def list_transactions():
    try:
        transactions = crud.get_all_transactions()
        return [record.get("t", record) for record in transactions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
def get_graph():
    """Get complete graph data for visualization"""
    try:
        return crud.get_graph_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/transactions")
def get_user_transactions(user_id: str):
    """Get all transactions for a specific user"""
    try:
        query = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)-[:SENT]->(t:Transaction)-[:RECEIVED_BY]->(r:User)
        RETURN u, t, r
        """
        result = db.query(query, {"user_id": user_id})
        return [{
            "u": dict(record["u"]) if record["u"] else None,
            "t": dict(record["t"]) if record["t"] else None,
            "r": dict(record["r"]) if record["r"] else None
        } for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transactions/{txn_id}")
def get_transaction(txn_id: str):
    """Get details of a specific transaction"""
    try:
        query = """
        MATCH (s:User)-[:SENT]->(t:Transaction {txn_id: $txn_id})-[:RECEIVED_BY]->(r:User)
        RETURN s, t, r
        """
        result = db.query(query, {"txn_id": txn_id})
        if not result:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return [{
            "s": dict(record["s"]) if record["s"] else None,
            "t": dict(record["t"]) if record["t"] else None,
            "r": dict(record["r"]) if record["r"] else None
        } for record in result]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sample-data")
def load_sample_data():
    """Load sample users and transactions for testing"""
    try:
        # Sample users
        sample_users = [
            {"user_id": "user1", "name": "Alice Johnson", "email": "alice@example.com", "phone": "+1234567890", "address": "123 Main St", "payment_method": "Credit Card"},
            {"user_id": "user2", "name": "Bob Smith", "email": "bob@example.com", "phone": "+1234567891", "address": "456 Oak Ave", "payment_method": "Bank Transfer"},
            {"user_id": "user3", "name": "Carol Davis", "email": "carol@example.com", "phone": "+1234567892", "address": "789 Pine Rd", "payment_method": "Digital Wallet"},
            {"user_id": "user4", "name": "David Wilson", "email": "david@example.com", "phone": "+1234567893", "address": "321 Elm St", "payment_method": "Credit Card"},
        ]
        
        # Sample transactions
        sample_transactions = [
            {"txn_id": "txn1", "sender_id": "user1", "receiver_id": "user2", "amount": 100.50, "device_id": "device1", "ip_address": "192.168.1.1"},
            {"txn_id": "txn2", "sender_id": "user2", "receiver_id": "user3", "amount": 250.75, "device_id": "device2", "ip_address": "192.168.1.2"},
            {"txn_id": "txn3", "sender_id": "user3", "receiver_id": "user4", "amount": 75.25, "device_id": "device3", "ip_address": "192.168.1.3"},
            {"txn_id": "txn4", "sender_id": "user1", "receiver_id": "user3", "amount": 500.00, "device_id": "device1", "ip_address": "192.168.1.1"},
            {"txn_id": "txn5", "sender_id": "user4", "receiver_id": "user1", "amount": 125.30, "device_id": "device4", "ip_address": "192.168.1.4"},
        ]
        
        # Create users
        for user_data in sample_users:
            crud.create_user(user_data)
        
        # Create transactions
        for txn_data in sample_transactions:
            crud.create_transaction(txn_data)
        
        return {"message": "Sample data loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend
frontend_path = os.path.join(os.path.dirname(__file__), '../frontend')
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/export/users/csv")
def export_users_csv(limit: int = 1000):
    rows = crud.get_all_users(limit)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id","name","email","phone","address","payment_method"])
    for r in rows:
        u = r.get("u") or r
        writer.writerow([u.get("user_id"), u.get("name"), u.get("email"), u.get("phone"), u.get("address"), u.get("payment_method")])
    output.seek(0)
    return StreamingResponse(io.StringIO(output.getvalue()), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=users.csv"})

@app.get("/export/transactions/json")
def export_transactions_json(limit: int = 1000):
    rows = crud.get_all_transactions(limit)
    txns = [ (r.get("t") or r) for r in rows ]
    return JSONResponse(content=txns)

@app.get("/analytics/shortest_path")
def shortest_path(u1: str, u2: str):
    # returns node id sequence between two users (if exists)
    query = """
    MATCH (a:User {user_id:$u1}), (b:User {user_id:$u2})
    CALL gds.alpha.shortestPath.stream({
      sourceNode: id(a),
      targetNode: id(b),
      relationshipWeightProperty: null
    }) YIELD nodeId
    RETURN nodeId
    """
    # NOTE: gds.alpha requires Graph Data Science lib; simpler fallback:
    fallback = """
    MATCH p=shortestPath((a:User {user_id:$u1})-[*]-(b:User {user_id:$u2}))
    RETURN [n IN nodes(p) | coalesce(n.user_id, n.txn_id)] AS path
    """
    res = db.query(fallback, {"u1": u1, "u2": u2})
    return res



