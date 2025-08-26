"""Tests for async pub/sub event system."""

import asyncio
import pytest
from sam_core.common.events import EventBus, Event, publish, subscribe, start_event_bus, stop_event_bus


class TestEventBus:
    """Test EventBus functionality."""
    
    @pytest.fixture
    def event_bus(self):
        """Create a fresh EventBus instance."""
        return EventBus()
    
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus):
        """Test basic publish and subscribe functionality."""
        await event_bus.start()
        
        # Subscribe to a topic
        events = []
        async for event in event_bus.subscribe("test_topic"):
            events.append(event)
            if len(events) >= 2:
                break
        
        # Publish events
        await event_bus.publish("test_topic", "test_payload_1")
        await event_bus.publish("test_topic", "test_payload_2")
        
        # Wait a bit for events to be processed
        await asyncio.sleep(0.1)
        
        await event_bus.stop()
        
        # Verify events
        assert len(events) == 2
        assert events[0].topic == "test_topic"
        assert events[0].payload == "test_payload_1"
        assert events[1].topic == "test_topic"
        assert events[1].payload == "test_payload_2"
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus):
        """Test multiple subscribers to the same topic."""
        await event_bus.start()
        
        # Create multiple subscribers
        events1 = []
        events2 = []
        
        async def subscriber1():
            async for event in event_bus.subscribe("multi_topic"):
                events1.append(event)
                if len(events1) >= 1:
                    break
        
        async def subscriber2():
            async for event in event_bus.subscribe("multi_topic"):
                events2.append(event)
                if len(events2) >= 1:
                    break
        
        # Start subscribers
        task1 = asyncio.create_task(subscriber1())
        task2 = asyncio.create_task(subscriber2())
        
        # Publish event
        await event_bus.publish("multi_topic", "shared_payload")
        
        # Wait for subscribers to process
        await asyncio.sleep(0.1)
        
        await event_bus.stop()
        await task1
        await task2
        
        # Both subscribers should have received the event
        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0].payload == "shared_payload"
        assert events2[0].payload == "shared_payload"
    
    @pytest.mark.asyncio
    async def test_topic_isolation(self, event_bus):
        """Test that events are isolated by topic."""
        await event_bus.start()
        
        events_topic1 = []
        events_topic2 = []
        
        async def subscriber_topic1():
            async for event in event_bus.subscribe("topic1"):
                events_topic1.append(event)
                if len(events_topic1) >= 1:
                    break
        
        async def subscriber_topic2():
            async for event in event_bus.subscribe("topic2"):
                events_topic2.append(event)
                if len(events_topic2) >= 1:
                    break
        
        # Start subscribers
        task1 = asyncio.create_task(subscriber_topic1())
        task2 = asyncio.create_task(subscriber_topic2())
        
        # Publish to different topics
        await event_bus.publish("topic1", "payload1")
        await event_bus.publish("topic2", "payload2")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        await event_bus.stop()
        await task1
        await task2
        
        # Each subscriber should only receive events from their topic
        assert len(events_topic1) == 1
        assert len(events_topic2) == 1
        assert events_topic1[0].payload == "payload1"
        assert events_topic2[0].payload == "payload2"
    
    @pytest.mark.asyncio
    async def test_publish_before_start(self, event_bus):
        """Test that publishing before start raises an error."""
        with pytest.raises(RuntimeError, match="EventBus not started"):
            await event_bus.publish("test", "payload")


class TestGlobalEventBus:
    """Test global event bus functions."""
    
    @pytest.mark.asyncio
    async def test_global_publish_subscribe(self):
        """Test global publish and subscribe functions."""
        await start_event_bus()
        
        events = []
        async for event in subscribe("global_topic"):
            events.append(event)
            if len(events) >= 1:
                break
        
        await publish("global_topic", "global_payload")
        
        await asyncio.sleep(0.1)
        await stop_event_bus()
        
        assert len(events) == 1
        assert events[0].topic == "global_topic"
        assert events[0].payload == "global_payload"