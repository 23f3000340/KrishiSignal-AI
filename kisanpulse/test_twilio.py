import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
auth_token  = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
from_number = os.environ.get("TWILIO_FROM_NUMBER", "").strip()

print("--- Twilio Credentials ---")
print(f"ACCOUNT_SID: {account_sid}")
print(f"AUTH_TOKEN:  {'*' * len(auth_token) if auth_token else 'Missing'}")
print(f"FROM_NUMBER: {from_number}")
print("--------------------------\n")

if not account_sid or not auth_token:
    print("[ERROR] Missing credentials in .env file.")
    exit(1)

try:
    client = Client(account_sid, auth_token)
    
    # 1. Fetch Account info
    account = client.api.accounts(account_sid).fetch()
    print("[SUCCESS] Connection successful!")
    print(f"Account Name: {account.friendly_name}")
    print(f"Account Status: {account.status}")
    print(f"Account Type: {account.type}\n")
    
    # 2. Fetch Purchased Phone Numbers
    print("--- Purchased Twilio Numbers ---")
    incoming_numbers = client.incoming_phone_numbers.list(limit=5)
    for num in incoming_numbers:
        print(f"Number: {num.phone_number} (SMS: {num.capabilities.get('sms')}, Voice: {num.capabilities.get('voice')})")
    print("---------------------------------\n")
    
    # 3. Fetch Verified Caller IDs
    print("--- Verified Caller IDs on Account ---")
    outgoing_caller_ids = client.outgoing_caller_ids.list(limit=20)
    if not outgoing_caller_ids:
        print("[WARNING] No verified caller IDs found on this account.")
    for cid in outgoing_caller_ids:
        print(f"Verified: {cid.phone_number} (Friendly Name: {cid.friendly_name})")
    print("--------------------------------------\n")
    
except Exception as e:
    print(f"[ERROR] Error communicating with Twilio: {e}")
