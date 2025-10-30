from fastapi import FastAPI
from .models import User, Transaction
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse, JSONResponse
import csv, io
import os
from . import crud, relationships

app = FastAPI(title="User & Transaction Graph API")

@app.post("/users")
def add_user(user: User):
    crud.create_user(user.dict())
    return {"message": f"User {user.user_id} added or updated."}

@app.post("/transactions")
def add_transaction(txn: Transaction):
    crud.create_transaction(txn.dict())
    return {"message": f"Transaction {txn.txn_id} added or updated."}

@app.get("/users")
def list_users():
    return crud.get_all_users()

@app.get("/transactions")
def list_transactions():
    return crud.get_all_transactions()

@app.get("/relationships/user/{user_id}")
def user_relationships(user_id: str):
    return relationships.get_user_relationships(user_id)

@app.get("/relationships/transaction/{txn_id}")
def transaction_relationships(txn_id: str):
    return relationships.get_transaction_relationships(txn_id)


frontend_path = os.path.join(os.path.dirname(__file__), '../frontend')
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/")
def serve_frontend():
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
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition":"attachment; filename=users.csv"})

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



