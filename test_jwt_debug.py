#!/usr/bin/env python3
"""
Debug JWT token issues
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def debug_jwt():
    """Debug JWT token creation and validation"""
    try:
        from src.auth.jwt import JWTHandler, create_tokens
        from src.config import settings
        from jose import jwt
        
        print("🔍 Debugging JWT Token Issues...")
        print("=" * 50)
        
        # Print current settings
        print(f"JWT Secret Key Length: {len(settings.jwt_secret_key)}")
        print(f"JWT Algorithm: {settings.jwt_algorithm}")
        print(f"JWT Access Token Expire Minutes: {settings.jwt_access_token_expire_minutes}")
        print(f"Current UTC Time: {datetime.utcnow()}")
        print()
        
        # Create a test token
        print("🔐 Creating test token...")
        test_data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "is_superuser": False
        }
        
        access_token = JWTHandler.create_access_token(test_data)
        print(f"✅ Token created: {access_token[:50]}...")
        print()
        
        # Decode the token without verification to check content
        print("🔍 Checking token content (unverified)...")
        unverified_payload = jwt.get_unverified_claims(access_token)
        print(f"Token payload: {json.dumps(unverified_payload, indent=2, default=str)}")
        
        # Check token expiration
        exp_timestamp = unverified_payload.get('exp')
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            current_time = datetime.utcnow()
            time_diff = exp_datetime - current_time
            
            print(f"Token expires at: {exp_datetime}")
            print(f"Current time: {current_time}")
            print(f"Time until expiry: {time_diff}")
            print(f"Seconds until expiry: {time_diff.total_seconds()}")
        print()
        
        # Try to verify the token immediately
        print("🔐 Verifying token immediately...")
        try:
            verified_payload = JWTHandler.verify_token(access_token)
            print("✅ Token verification successful!")
            print(f"Verified payload: {json.dumps(verified_payload, indent=2, default=str)}")
        except Exception as e:
            print(f"❌ Token verification failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ JWT debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_jwt()