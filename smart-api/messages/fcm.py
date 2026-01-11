import firebase_admin
from firebase_admin import credentials, messaging
from typing import Dict, Any, Optional
import os
from pathlib import Path
import json

class FCMService:
    _initialized = False
    
    @classmethod
    def initialize_firebase(cls):
        """Initialize Firebase Admin SDK"""
        if cls._initialized:
            return True
        
        try:
            # Try multiple possible locations for the Firebase credentials
            current_dir = Path(__file__).parent.absolute()
            possible_paths = [
                current_dir.parent / os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
                
            ]
            
            cred_path = None
            print("current_dir:", current_dir)
            print(current_dir.parent,"parent")
            for path in possible_paths:
                if Path(path).exists():
                    cred_path = path
                    print(f"✅ Found Firebase credentials at: {path}")
                    break
            
            if not cred_path:
                # Try to get from environment variable as JSON string
                cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
                if cred_json:
                    try:
                        cred_dict = json.loads(cred_json)
                        cred = credentials.Certificate(cred_dict)
                        firebase_admin.initialize_app(cred)
                        cls._initialized = True
                        print("✅ Firebase initialized from environment variable")
                        return True
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON in FIREBASE_CREDENTIALS_JSON: {e}")
                else:
                    print("❌ Firebase credentials file not found and no environment variable set")
                return False
            
            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            print("✅ Firebase initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            return False
    
    @staticmethod
    def send_message_notification(
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send push notification for new message"""
        if not fcm_token:
            print("❌ No FCM token provided")
            return False
        
        # Initialize Firebase if not already done
        if not FCMService._initialized:
            if not FCMService.initialize_firebase():
                print("❌ Failed to initialize Firebase")
                return False
        
        try:
            # Build the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title[:50],  # Truncate if too long
                    body=body[:100],
                ),
                data=data or {},
                token=fcm_token,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            content_available=True,
                            sound="default",
                            badge=1
                        )
                    )
                ),
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="messages",
                        sound="default",
                        icon="notification_icon",
                        color="#FF0000",
                        click_action="FLUTTER_NOTIFICATION_CLICK"
                    )
                )
            )
            
            # Send the message
            response = messaging.send(message)
            print(f"✅ FCM message sent successfully: {response}")
            return True
            
        except messaging.UnregisteredError:
            print(f"❌ FCM token is no longer valid: {fcm_token}")
            return False
        except Exception as e:
            print(f"❌ Error sending FCM message: {e}")
            return False

# Initialize Firebase on module import
FCMService.initialize_firebase()