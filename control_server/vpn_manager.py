from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import base64

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

    return {"private_key": private_b64, "public_key": public_b64}

if __name__ == "__main__":
    keys = generate_key_pair()
    print("Private Key:", keys["private_key"])
    print("Public Key :", keys["public_key"])