# integrity_validator.py

import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Optional

# --- 1. Key Management and Persistence ---

def generate_keys() -> Tuple[rsa.RSAPrivateNumbers, rsa.RSAPublicNumbers]:
    """Generates a new RSA private and public key pair."""
    # Generate a secure 2048-bit RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    return private_key, private_key.public_key()

def save_private_key(private_key: rsa.RSAPrivateKey, filename: str = "private.pem"):
    """Saves the private key securely (requires a password)."""
    password = b"strong-security-password" 
    
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        # Securely encrypt the private key using AES-256
        encryption_algorithm=serialization.BestAvailableEncryption(password)
    )
    with open(filename, "wb") as f:
        f.write(pem)
    print(f"🔑 Private key saved to {filename} (Encrypted).")

def load_private_key(filename: str = "private.pem") -> rsa.RSAPrivateKey:
    """Loads the private key, requiring the password."""
    password = b"strong-security-password"
    with open(filename, "rb") as f:
        pem = f.read()
    
    private_key = serialization.load_pem_private_key(
        pem,
        password=password,
        backend=default_backend()
    )
    return private_key

def save_public_key(public_key: rsa.RSAPublicKey, filename: str = "public.pem"):
    """Saves the public key (unencrypted)."""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(filename, "wb") as f:
        f.write(pem)
    print(f"🗝️ Public key saved to {filename}.")

def load_public_key(filename: str = "public.pem") -> rsa.RSAPublicKey:
    """Loads the public key."""
    with open(filename, "rb") as f:
        pem = f.read()
    public_key = serialization.load_pem_public_key(
        pem,
        backend=default_backend()
    )
    return public_key

# --- 2. Signing and Verification Logic ---

def sign_data(data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Creates a digital signature of the data using the private key.
    This process first hashes the data (SHA256) and then encrypts the hash.
    """
    # Use PKCS1 v1.5 padding and SHA256 for a secure signature
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print(f"✍️ Data signed successfully.")
    return signature

def verify_signature(data: bytes, signature: bytes, public_key: rsa.RSAPublicKey) -> bool:
    """
    Verifies the digital signature using the public key.
    If the file has been tampered with or the signature is invalid, verification fails.
    """
    try:
        # This function will raise an exception if the signature is invalid
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Verification FAILED. Reason: {e}")
        return False

# --- 3. File Utility ---

def create_test_file(filename: str, content: str):
    """Creates a temporary file for testing the integrity."""
    with open(filename, "w") as f:
        f.write(content)
    print(f"💾 Created test file: {filename}")

def tamper_with_file(filename: str):
    """Simulates a malicious actor modifying the file."""
    with open(filename, "a") as f:
        f.write("\n\n[INJECTED MALICIOUS CODE HERE]")
    print(f"🚨 Tampered with file: {filename}")

def read_file_as_bytes(filename: str) -> bytes:
    """Reads file content for hashing and signing."""
    with open(filename, "rb") as f:
        return f.read()

# --- Main Execution ---

async def main():
    
    FILE_NAME = "important_document.txt"
    SIG_FILE = "document.sig"
    
    # 1. Setup: Generate and save keys
    private_key, public_key = generate_keys()
    save_private_key(private_key)
    save_public_key(public_key)
    
    # 2. Create the Original Document
    original_content = "This is the secure original data. Hash: A8B9C0D1"
    create_test_file(FILE_NAME, original_content)
    original_data = read_file_as_bytes(FILE_NAME)

    # 3. Signing Process (Done by the sender/author)
    print("\n--- Signing the Original File ---")
    signature = sign_data(original_data, private_key)
    
    # Save the signature to a file
    with open(SIG_FILE, "wb") as f:
        f.write(signature)
    print(f"📝 Signature saved to {SIG_FILE}")

    # --- Scenario 1: Successful Verification (Integrity Intact) ---
    
    # 4. Verification Process (Done by the receiver)
    print("\n--- SCENARIO 1: Verification of Intact File ---")
    
    # Load the public key to verify (Public keys are safe to share)
    public_key_loaded = load_public_key()
    data_to_verify = read_file_as_bytes(FILE_NAME)
    signature_to_verify = signature # Use the signature we just created
    
    if verify_signature(data_to_verify, signature_to_verify, public_key_loaded):
        print("✅ SUCCESS: The file's integrity is verified. It is authentic and untampered.")
    else:
        print("❌ FAILURE: Verification failed.")

    # --- Scenario 2: Failed Verification (File Tampered) ---
    
    print("\n--- SCENARIO 2: Verification of Tampered File ---")
    
    # Simulate an attack: modify the file AFTER it was signed
    tamper_with_file(FILE_NAME)
    
    # Try to verify the tampered file using the original signature
    tampered_data = read_file_as_bytes(FILE_NAME)
    
    if verify_signature(tampered_data, signature_to_verify, public_key_loaded):
        print("❌ CRITICAL FAILURE: Verification succeeded despite tampering!")
    else:
        print("✅ SUCCESS (Defensive): Verification failed due to tampering. Data integrity loss detected.")
    
    # Cleanup keys and file
    os.remove(FILE_NAME)
    os.remove(SIG_FILE)
    os.remove("private.pem")
    os.remove("public.pem")
    print("\n🧹 Cleaned up temporary files.")

if __name__ == "__main__":
    # Note: No asyncio used here, but keeping the main structure similar for consistency
    import asyncio
    asyncio.run(main())