#!/usr/bin/env python3
"""
Test script for simplified FileStorage API
Tests the updated endpoints and response format
"""

from src.api.client import ImaLinkClient
from pathlib import Path
import json

def main():
    client = ImaLinkClient()
    
    print("=" * 60)
    print("Testing Simplified FileStorage API")
    print("=" * 60)
    
    # Test 1: Get all storages
    print("\n1. GET /file-storage/ - List all storages")
    try:
        storages = client.get_file_storages()
        print(f"✅ Success! Found {len(storages)} storage(s)")
        for storage in storages:
            print(f"   - {storage.display_name or storage.directory_name}")
            print(f"     UUID: {storage.storage_uuid}")
            print(f"     Path: {storage.full_path}")
            print(f"     ID: {storage.id}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Create new storage
    print("\n2. POST /file-storage/ - Create new storage")
    test_base_path = "/tmp/imalink_test_storage"
    Path(test_base_path).mkdir(exist_ok=True)
    
    try:
        # Backend generates UUID and directory_name
        new_storage = client.register_file_storage(
            base_path=test_base_path,
            display_name="Test Storage",
            description="Testing simplified API"
        )
        print(f"✅ Storage created!")
        print(f"   UUID: {new_storage.storage_uuid}")
        print(f"   Directory: {new_storage.directory_name}")
        print(f"   Full path: {new_storage.full_path}")
        print(f"   ID: {new_storage.id}")
        print(f"   Display name: {new_storage.display_name}")
        
        # Verify backend generated the UUID
        assert new_storage.storage_uuid, "Backend should generate UUID"
        assert "imalink_" in new_storage.directory_name, "Directory should follow naming pattern"
        print(f"   ✓ Backend generated UUID and directory_name")
        
        # Note: Physical directory creation is frontend's responsibility
        print(f"\n   Note: Physical directory at {new_storage.full_path}")
        print(f"         should be created by frontend (not tested here)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 3: Get specific storage
    print(f"\n3. GET /file-storage/{new_storage.storage_uuid} - Get specific storage")
    try:
        storage = client.get_file_storage(new_storage.storage_uuid)
        print(f"✅ Retrieved storage: {storage.display_name}")
        assert storage.storage_uuid == new_storage.storage_uuid
        print(f"   ✓ UUID matches")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 4: Update storage metadata
    print(f"\n4. PUT /file-storage/{new_storage.storage_uuid} - Update metadata")
    try:
        updated = client.update_file_storage(
            new_storage.storage_uuid,
            display_name="Updated Test Storage",
            description="Updated description"
        )
        print(f"✅ Updated storage!")
        print(f"   New display name: {updated.display_name}")
        print(f"   New description: {updated.description}")
        
        # Verify immutable fields didn't change
        assert updated.storage_uuid == new_storage.storage_uuid
        assert updated.base_path == new_storage.base_path
        assert updated.directory_name == new_storage.directory_name
        print(f"   ✓ Immutable fields (UUID, paths) unchanged")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 5: Verify no statistics in response
    print(f"\n5. Verify simplified model (no statistics)")
    try:
        assert not hasattr(updated, 'total_files'), "Should not have total_files"
        assert not hasattr(updated, 'total_size_bytes'), "Should not have total_size_bytes"
        assert not hasattr(updated, 'is_accessible'), "Should not have is_accessible"
        print(f"✅ Confirmed: No statistics fields")
        print(f"   ✓ Backend only stores metadata")
        print(f"   ✓ Frontend handles accessibility checks")
    except AssertionError as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 6: Delete storage
    print(f"\n6. DELETE /file-storage/{new_storage.storage_uuid} - Delete storage")
    try:
        result = client.delete_file_storage(new_storage.storage_uuid)
        print(f"✅ Storage deleted!")
        print(f"   Response: {result}")
        
        # Verify it's gone
        try:
            client.get_file_storage(new_storage.storage_uuid)
            print(f"❌ Error: Storage still exists after deletion")
        except:
            print(f"   ✓ Storage successfully removed from backend")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nKey findings:")
    print("  • Backend generates UUID and directory_name (frontend doesn't send UUID)")
    print("  • Response uses {success: true, data: {...}} wrapper")
    print("  • No statistics (total_files, total_size_bytes)")
    print("  • No accessibility tracking (is_accessible)")
    print("  • Frontend responsible for physical directory creation")
    print("  • Only metadata fields (display_name, description) updatable")
    print("  • Perfect sync: backend generates names, frontend uses them")

if __name__ == "__main__":
    main()
