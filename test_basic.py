#!/usr/bin/env python3
"""Basic functionality test."""

import sys
sys.path.insert(0, 'src')

from sam_core import (
    LocalJSONLStore,
    generate_trace_id,
    utcnow,
    DecisionTrace,
    DecodingMode
)

def test_basic():
    """Test basic functionality."""
    print("Testing basic functionality...")
    
    # Test ID generation
    trace_id = generate_trace_id()
    print(f"✅ Generated trace ID: {trace_id}")
    
    # Test time utilities
    now = utcnow()
    print(f"✅ Current UTC time: {now}")
    
    # Test state store
    store = LocalJSONLStore(".test_state")
    store.set("test_key", "test_value")
    value = store.get("test_key")
    print(f"✅ State store test: {value}")
    
    # Test decision trace creation
    trace = DecisionTrace(
        trace_id=trace_id,
        started_at=now,
        goal="Test goal",
        maturity_level=5,
        mental_health=0.8,
        pmx_affect={"joy": 0.6},
        decoding_mode=DecodingMode.REASONING,
        confidence=0.9
    )
    print(f"✅ Created decision trace: {trace.goal}")
    
    print("✅ All basic tests passed!")

if __name__ == "__main__":
    test_basic()