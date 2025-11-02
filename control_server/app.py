
import webbrowser
import threading
import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vpn_manager import (
    add_user,
    delete_user_from_db,
    delete_user_from_vpn_conf,
    list_users,
    update_vpn_gateway_config,
    create_vpn_gateway_config,
    generate_key_pair,
    init_db,get_public_key_from_db,
)
import os

# --- CONFIGURATION ---
DB_PATH = "../database/users.db"
WG_CONFIG_PATH = "../vpn_gateway/wg0.conf"
VPN_GW_ENDPOINT = "vpn.example.com:51820"
VPN_GW_PRIVATE_KEY, VPN_GW_PUBLIC_KEY = generate_key_pair()

# Initialize database on startup
init_db()
create_vpn_gateway_config(WG_CONFIG_PATH, VPN_GW_PRIVATE_KEY, 51820, "10.8.0.1/24")

app = FastAPI(title="VPN Control Server", version="1.0.0")

# --- MODELS ---
class UserCreate(BaseModel):
    username: str
    allowed_ips: str

# --- ROUTES ---

def open_docs():
    """Open the FastAPI Swagger docs in your default browser."""
    webbrowser.open_new_tab("http://127.0.0.1:8000/docs")

@app.get("/")
def root():
    return {"status": "ok", "message": "VPN Control Server running"}

@app.get("/users")
def get_users():
    users = list_users(DB_PATH)
    return {"count": len(users), "users": users}

@app.post("/users")
def create_user(data: UserCreate):
    # Add new VPN client
    try:
        user_config = add_user(
            vpn_gw_public_key=VPN_GW_PUBLIC_KEY,
            vpn_gw_endpoint=VPN_GW_ENDPOINT,
            username=data.username,
            allowed_ips=data.allowed_ips,
        )
        update_vpn_gateway_config(
            WG_CONFIG_PATH,
            data.username,
            user_config["public_key"],
            data.allowed_ips,
        )
        return {"message": "User created", "config": user_config}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{username}")
def delete_user(username: str):

    delete_user_from_vpn_conf(username, WG_CONFIG_PATH,DB_PATH)
    delete_user_from_db(username, DB_PATH)
 
    return {"message": f"User '{username}' deleted successfully"}

if __name__ == "__main__":
    # Open browser after 1 second (so the server has time to start)
    threading.Timer(1.0, open_docs).start()
    
    # Run FastAPI using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)