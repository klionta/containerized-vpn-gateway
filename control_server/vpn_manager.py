from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import base64
import sqlite3
import os

#Generate a private/public key pair for a client or server
def generate_key_pair():
    """
    Generate a Curve25519 (X25519) key pair for VPN client or server.

    Returns:
        dict: {
            "private_key": base64 encoded private key,
            "public_key": base64 encoded public key
        }
    """
    # Generate private key
    private_key = x25519.X25519PrivateKey.generate()

    # Derive public key
    public_key = private_key.public_key()

    # Serialize keys to raw bytes
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # Encode keys to base64 strings for storage/config
    private_b64 = base64.b64encode(private_bytes).decode('utf-8')
    public_b64 = base64.b64encode(public_bytes).decode('utf-8')

    return  private_b64, public_b64




def init_db():

    conn = sqlite3.connect("../database/users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            allowed_ips TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_user(vpn_gw_public_key,vpn_gw_endpoint,username, allowed_ips) :
    """
    Add a new VPN client:
    - Generate key pair
    - Store in database
    - Prepare client config dictionary
    """

    # 1️⃣ Generate client key pair
    client_private_key,client_public_key=generate_key_pair()

    # 2️⃣ Store user in database
    conn = sqlite3.connect("../database/users.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (username, private_key, public_key, allowed_ips)
        VALUES (?, ?, ?, ?)
    """, (username, client_private_key, client_public_key, allowed_ips))

    conn.commit()
    conn.close()

   

    client_config = {
        "username": username,
        "private_key": client_private_key,
        "public_key": client_public_key,
        "server_public_key": vpn_gw_public_key,
        "allowed_ips": allowed_ips,
        "endpoint": vpn_gw_endpoint
    }

    print(f"✅ User '{username}' added to database.")
    return client_config


def delete_user_from_db(username,db_path) :

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT public_key FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if not result:
        print(f"⚠️ User '{username}' not found in database.")
        conn.close()
        return False

    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    print(f"✅ User '{username}' removed from database.")



def create_vpn_gateway_config(WG_CONFIG_PATH,vpn_private_key,listen_port,address_space):
    
    # Creates a VPN gateway config file

    if not os.path.exists(WG_CONFIG_PATH):
        with open(WG_CONFIG_PATH, "w") as f:
            f.write("# VPN config file!\n")
            f.write("[Interface]\n")
            f.write(f"Address = {address_space}\n")
            f.write(f"PrivateKey = {vpn_private_key}\n")
            f.write(f"ListenPort = {listen_port}\n")


    return WG_CONFIG_PATH

    

def update_vpn_gateway_config(WG_CONFIG_PATH ,username, client_public_key, allowed_ips):
    """
    Add a new client peer to the WireGuard VPN gateway config file.

    Args:
        username (str): Client name, used as a comment
        client_public_key (str): Base64 public key of the client
        allowed_ips (str): Client IPs in CIDR format, e.g. '10.8.0.2/32'
    """

  
    with open(WG_CONFIG_PATH) as f:
        content=f.read()
        if client_public_key in content:
            print(f"The client {username} already exists!")
            return
    
    with open(WG_CONFIG_PATH,"a") as f:
        f.write("\n")
        f.write("\n")
        f.write("[Peer]\n")
        f.write(f"# {username}\n")
        f.write(f"PublicKey = {client_public_key}\n")
        f.write(f"AllowedIPs = {allowed_ips}\n")

    print(f"✅ User '{username}' added to VPN config.")
    return

def delete_user_from_vpn_conf(user_config,wg_config_path):
    f= open(wg_config_path,"r")
    lines=f.readlines()
    lines_to_remove=[]
    
    i=0
    for line in lines:
        i+=1
        line=line.strip()
        if user_config["public_key"] in line:
            lines_to_remove=[i-3,i-2,i-1,i]

    f.close()

    with open(wg_config_path,"w") as fw:
        for i in range(len(lines)):
            if i not in lines_to_remove:
                fw.write(lines[i])

    username=user_config["username"]
    print(f"✅ User '{username}' removed from VPN config.")


if __name__ == "__main__":

    WG_CONFIG_PATH = "../vpn_gateway/wg0.conf"
    DB_PATH="../database/users.db"
    vpn_gw_endpoint = "vpn.example.com:51820"
    vpn_gw_public_key,vpn_gw_private_key = generate_key_pair()

    init_db()
    create_vpn_gateway_config(WG_CONFIG_PATH,vpn_gw_private_key,51820,"10.0.0.0/8")
 
    user_config = add_user(vpn_gw_public_key,vpn_gw_endpoint,"alice", "10.8.0.2/32") 
    update_vpn_gateway_config(WG_CONFIG_PATH ,user_config["username"], user_config["public_key"], user_config["allowed_ips"])

    delete_user_from_db("alice",DB_PATH)
    delete_user_from_vpn_conf(user_config,WG_CONFIG_PATH)