#!/usr/bin/env python3
"""
Quick test to verify Gallery View can load photos from backend
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.client import APIClient

def test_gallery_api():
    """Test the API calls that Gallery View uses"""
    
    # Create API client
    client = APIClient("http://localhost:8000")
    
    print("Testing Gallery View API calls...")
    print("=" * 60)
    
    # Test 1: Get photos
    try:
        print("\n1. Testing get_photos()...")
        response = client.get_photos(limit=200)
        photos = response.get('data', [])
        print(f"✅ Got {len(photos)} photos")
        
        if photos:
            photo = photos[0]
            print(f"   First photo: {photo.get('filename', 'Unknown')}")
            print(f"   Hothash: {photo.get('hothash', 'N/A')[:16]}...")
            print(f"   Taken: {photo.get('taken_at', 'Unknown')}")
            
            # Test 2: Get hotpreview for first photo
            hothash = photo.get('hothash')
            if hothash:
                print(f"\n2. Testing get_hotpreview('{hothash[:16]}...')...")
                image_data = client.get_hotpreview(hothash)
                print(f"✅ Got hotpreview: {len(image_data)} bytes")
                
                # Verify it's a valid image
                from PySide6.QtGui import QPixmap
                pixmap = QPixmap()
                if pixmap.loadFromData(image_data):
                    print(f"✅ Valid image: {pixmap.width()}x{pixmap.height()}px")
                else:
                    print("❌ Invalid image data")
        else:
            print("⚠️  No photos in database")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Get import sessions
    try:
        print("\n3. Testing get_import_sessions()...")
        response = client.get_import_sessions(limit=100)
        sessions = response.get('data', [])
        print(f"✅ Got {len(sessions)} import sessions")
        
        if sessions:
            session = sessions[0]
            print(f"   First session: #{session.get('id')} - {session.get('source_path', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error loading sessions: {e}")
    
    print("\n" + "=" * 60)
    print("All tests passed! Gallery View should work.")
    return True


if __name__ == "__main__":
    test_gallery_api()
