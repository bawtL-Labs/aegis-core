"""Tests for StateStore interface and LocalJSONLStore implementation."""

import json
import tempfile
import shutil
from pathlib import Path
import pytest

from sam_core.common.state_store import StateStore, LocalJSONLStore


class TestLocalJSONLStore:
    """Test LocalJSONLStore implementation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def store(self, temp_dir):
        """Create a LocalJSONLStore instance."""
        return LocalJSONLStore(temp_dir)
    
    def test_set_and_get(self, store):
        """Test setting and getting values."""
        # Test basic set/get
        store.set("test_key", "test_value")
        assert store.get("test_key") == "test_value"
        
        # Test complex data
        complex_data = {"nested": {"value": 42}, "list": [1, 2, 3]}
        store.set("complex_key", complex_data)
        assert store.get("complex_key") == complex_data
        
        # Test None for non-existent key
        assert store.get("non_existent") is None
    
    def test_cache_behavior(self, store):
        """Test that cache works correctly."""
        store.set("cache_test", "cached_value")
        
        # Should be in cache
        assert store.get("cache_test") == "cached_value"
        
        # Create new store instance to test file persistence
        new_store = LocalJSONLStore(store.base_path)
        assert new_store.get("cache_test") == "cached_value"
    
    def test_append_jsonl(self, store):
        """Test JSONL append functionality."""
        # Append some test data
        test_data = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        
        for item in test_data:
            store.append_jsonl("test_log", item)
        
        # Check file was created
        log_file = store.base_path / "test_log.jsonl"
        assert log_file.exists()
        
        # Read and verify content
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        assert json.loads(lines[0]) == test_data[0]
        assert json.loads(lines[1]) == test_data[1]
    
    def test_rotate_jsonl(self, store):
        """Test JSONL rotation functionality."""
        # Create a large JSONL file
        large_data = {"data": "x" * 1000}  # ~1KB per line
        
        # Add enough data to trigger rotation (assuming 100MB limit)
        for i in range(100):  # This should be enough to trigger rotation
            store.append_jsonl("large_log", large_data)
        
        # Trigger rotation
        store.rotate("large_log", max_mb=1, max_files=3)
        
        # Check that compressed files were created
        compressed_files = list(store.base_path.glob("large_log.*.jsonl.gz"))
        assert len(compressed_files) > 0
        
        # Check that original file was cleared
        original_file = store.base_path / "large_log.jsonl"
        if original_file.exists():
            assert original_file.stat().st_size == 0


class TestStateStoreInterface:
    """Test StateStore interface compliance."""
    
    def test_interface_methods(self):
        """Test that LocalJSONLStore implements all required methods."""
        store = LocalJSONLStore()
        
        # Check that all abstract methods are implemented
        assert hasattr(store, 'get')
        assert hasattr(store, 'set')
        assert hasattr(store, 'append_jsonl')
        assert hasattr(store, 'rotate')
        
        # Check that methods are callable
        assert callable(store.get)
        assert callable(store.set)
        assert callable(store.append_jsonl)
        assert callable(store.rotate)