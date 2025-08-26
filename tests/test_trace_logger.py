"""Tests for TraceLogger functionality."""

import asyncio
import tempfile
import shutil
import json
from pathlib import Path
import pytest
from datetime import datetime

from sam_core.tracing.logger import TraceLogger
from sam_core.tracing.models import DecisionTrace, DecodingMode
from sam_core.common.state_store import LocalJSONLStore
from sam_core.common.ids import generate_trace_id


class TestTraceLogger:
    """Test TraceLogger functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def state_store(self, temp_dir):
        """Create a LocalJSONLStore instance."""
        return LocalJSONLStore(temp_dir)
    
    @pytest.fixture
    def trace_logger(self, state_store):
        """Create a TraceLogger instance."""
        return TraceLogger(state_store, "test_traces")
    
    @pytest.fixture
    def sample_trace(self):
        """Create a sample decision trace."""
        return DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Test decision",
            maturity_level=5,
            mental_health=0.8,
            pmx_affect={"joy": 0.6, "fear": 0.2},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.85
        )
    
    @pytest.mark.asyncio
    async def test_log_trace_async(self, trace_logger, sample_trace):
        """Test async trace logging."""
        await trace_logger.start()
        
        # Log a trace
        await trace_logger.log_trace(sample_trace)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        await trace_logger.stop()
        
        # Check that trace was written to file
        trace_file = trace_logger.state_store.base_path / "test_traces.jsonl"
        assert trace_file.exists()
        
        # Read and verify content
        with open(trace_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        trace_data = json.loads(lines[0])
        assert trace_data["goal"] == "Test decision"
        assert trace_data["maturity_level"] == 5
        assert trace_data["mental_health"] == 0.8
    
    def test_log_trace_sync(self, trace_logger, sample_trace):
        """Test synchronous trace logging fallback."""
        # Log without starting the logger
        trace_logger._log_trace_sync(sample_trace)
        
        # Check that trace was written to file
        trace_file = trace_logger.state_store.base_path / "test_traces.jsonl"
        assert trace_file.exists()
        
        # Read and verify content
        with open(trace_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        trace_data = json.loads(lines[0])
        assert trace_data["goal"] == "Test decision"
    
    @pytest.mark.asyncio
    async def test_multiple_traces(self, trace_logger):
        """Test logging multiple traces."""
        await trace_logger.start()
        
        # Create multiple traces
        traces = []
        for i in range(3):
            trace = DecisionTrace(
                trace_id=generate_trace_id(),
                started_at=datetime.now(),
                goal=f"Test decision {i}",
                maturity_level=i + 1,
                mental_health=0.8,
                pmx_affect={"joy": 0.6},
                decoding_mode=DecodingMode.REASONING,
                confidence=0.85
            )
            traces.append(trace)
        
        # Log all traces
        for trace in traces:
            await trace_logger.log_trace(trace)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        await trace_logger.stop()
        
        # Check that all traces were written
        trace_file = trace_logger.state_store.base_path / "test_traces.jsonl"
        with open(trace_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        # Verify each trace
        for i, line in enumerate(lines):
            trace_data = json.loads(line)
            assert trace_data["goal"] == f"Test decision {i}"
            assert trace_data["maturity_level"] == i + 1
    
    @pytest.mark.asyncio
    async def test_trace_with_finished_at(self, trace_logger):
        """Test that finished_at is set if not provided."""
        await trace_logger.start()
        
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Test decision",
            maturity_level=5,
            mental_health=0.8,
            pmx_affect={"joy": 0.6},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.85
        )
        
        # Trace doesn't have finished_at set
        assert trace.finished_at is None
        
        await trace_logger.log_trace(trace)
        await asyncio.sleep(0.1)
        await trace_logger.stop()
        
        # Check that finished_at was set
        trace_file = trace_logger.state_store.base_path / "test_traces.jsonl"
        with open(trace_file, 'r') as f:
            line = f.readline()
        
        trace_data = json.loads(line)
        assert "finished_at" in trace_data
        assert trace_data["finished_at"] is not None