#!/usr/bin/env python3
"""
Golden Path Example - Integration of Aegis Core with PMX, Scaffolding, and SDE.

This example demonstrates how the three components of the Aegis trilogy
integrate through the core contracts and plumbing.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import sys
sys.path.insert(0, 'src')

# Core imports
from sam_core import (
    LocalJSONLStore,
    TraceLogger,
    SelfGovernancePolicy,
    DecisionTrace,
    DecodingMode,
    generate_trace_id,
    utcnow,
    start_event_bus,
    stop_event_bus,
    publish
)

# Contract imports (these would be implemented by the actual repos)
from sam_core.contracts.pmx import PMXInterface, AffectSnapshot, Traits
from sam_core.contracts.scaffolding import ScaffoldingInterface, IdentitySnapshot
from sam_core.contracts.sde import SDEInterface, DecisionRequest, DecisionResult


class MockPMX(PMXInterface):
    """Mock PMX implementation for demonstration."""
    
    def __init__(self):
        self.traits = Traits(
            openness=0.7,
            conscientiousness=0.8,
            extraversion=0.4,
            agreeableness=0.9,
            neuroticism=0.2
        )
        self.affect = AffectSnapshot(
            joy=0.6,
            fear=0.1,
            sadness=0.0,
            anger=0.0,
            surprise=0.2,
            disgust=0.0
        )
    
    def get_traits(self) -> Traits:
        return self.traits
    
    def get_affect_snapshot(self) -> AffectSnapshot:
        return self.affect
    
    def update_affect(self, stimulus: str, intensity: float) -> AffectSnapshot:
        # Simple affect update logic
        if "positive" in stimulus.lower():
            self.affect.joy = min(1.0, self.affect.joy + intensity * 0.1)
        elif "negative" in stimulus.lower():
            self.affect.fear = min(1.0, self.affect.fear + intensity * 0.1)
        return self.affect
    
    def get_boundary_manager(self):
        # Mock boundary manager
        return None
    
    def is_stable(self) -> bool:
        return True


class MockScaffolding(ScaffoldingInterface):
    """Mock Scaffolding implementation for demonstration."""
    
    def __init__(self):
        self.identity = IdentitySnapshot(
            core_values=["Safety", "Helpfulness", "Honesty"],
            goals=["Assist users effectively", "Maintain system stability"],
            constraints=["Do no harm", "Respect privacy"],
            preferences={"communication_style": "clear_and_helpful"},
            self_model={"capabilities": ["reasoning", "learning", "adaptation"]}
        )
        self.memories = []
        self.plans = []
    
    def store_observation(self, observation) -> str:
        obs_id = f"obs_{len(self.memories)}"
        self.memories.append(observation)
        return obs_id
    
    def retrieve_memories(self, query: str, limit: int = 10):
        # Simple keyword matching
        relevant = []
        for memory in self.memories[-limit:]:
            if any(word in memory.content.lower() for word in query.lower().split()):
                relevant.append(memory)
        return relevant
    
    def create_plan(self, goal: str, context: Dict[str, Any]) -> str:
        plan_id = f"plan_{len(self.plans)}"
        # Mock plan creation
        return plan_id
    
    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> None:
        pass
    
    def get_plan_summary(self, plan_id: str):
        return None
    
    def get_active_plans(self):
        return []
    
    def get_identity_snapshot(self) -> IdentitySnapshot:
        return self.identity
    
    def update_identity(self, updates: Dict[str, Any]) -> None:
        pass


class MockSDE(SDEInterface):
    """Mock SDE implementation for demonstration."""
    
    def __init__(self):
        self.decision_history = []
    
    def make_decision(self, request: DecisionRequest) -> DecisionResult:
        # Simple decision logic
        if "safety" in request.goal.lower():
            selected_option = "prioritize_safety"
            confidence = 0.9
        elif "efficiency" in request.goal.lower():
            selected_option = "optimize_performance"
            confidence = 0.8
        else:
            selected_option = "balanced_approach"
            confidence = 0.7
        
        result = DecisionResult(
            request_id=request.request_id,
            selected_option=selected_option,
            reasoning=f"Selected {selected_option} based on goal analysis",
            confidence=confidence,
            execution_plan={"steps": ["analyze", "execute", "monitor"]}
        )
        
        self.decision_history.append(result)
        return result
    
    def get_decision_options(self, request: DecisionRequest):
        return []
    
    def evaluate_option(self, option_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"utility": 0.5, "risks": [], "requirements": []}
    
    def get_decision_history(self, limit: int = 100):
        return self.decision_history[-limit:]
    
    def update_decision_model(self, feedback: Dict[str, Any]) -> None:
        pass


class AegisCore:
    """Main integration class that ties all components together."""
    
    def __init__(self, state_path: str = ".sam_state"):
        # Initialize core components
        self.state_store = LocalJSONLStore(state_path)
        self.trace_logger = TraceLogger(self.state_store, "traces")
        self.policy = SelfGovernancePolicy()
        
        # Initialize external components
        self.pmx = MockPMX()
        self.scaffolding = MockScaffolding()
        self.sde = MockSDE()
        
        # State
        self.maturity_level = 6
        self.mental_health = 0.85
    
    async def start(self):
        """Start the Aegis Core system."""
        await start_event_bus()
        await self.trace_logger.start()
        
        # Publish system start event
        await publish("aegis.system.start", {
            "timestamp": utcnow().isoformat(),
            "maturity_level": self.maturity_level,
            "mental_health": self.mental_health
        })
    
    async def stop(self):
        """Stop the Aegis Core system."""
        await self.trace_logger.stop()
        await stop_event_bus()
    
    async def make_decision(self, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a decision through the integrated system."""
        if context is None:
            context = {}
        
        # Generate trace ID
        trace_id = generate_trace_id()
        started_at = utcnow()
        
        # Get current state from components
        pmx_affect_snapshot = self.pmx.get_affect_snapshot()
        identity = self.scaffolding.get_identity_snapshot()
        
        # Create decision request
        request = DecisionRequest(
            request_id=trace_id,
            goal=goal,
            context=context,
            constraints=identity.constraints,
            compute_budget=1000,
            time_budget_ms=5000
        )
        
        # Create decision trace
        trace = DecisionTrace(
            trace_id=trace_id,
            started_at=started_at,
            goal=goal,
            context=context,
            constraints=identity.constraints,
            compute_budget=request.compute_budget,
            time_budget_ms=request.time_budget_ms,
            maturity_level=self.maturity_level,
            mental_health=self.mental_health,
            pmx_affect={
                "anger": pmx_affect_snapshot.anger,
                "fear": pmx_affect_snapshot.fear,
                "sadness": pmx_affect_snapshot.sadness,
                "joy": pmx_affect_snapshot.joy,
                "surprise": pmx_affect_snapshot.surprise,
                "disgust": pmx_affect_snapshot.disgust,
                **pmx_affect_snapshot.custom_affects
            },
            decoding_mode=DecodingMode.REASONING,
            confidence=0.8
        )
        
        # Apply policy review
        policy_decision = self.policy.review(trace)
        
        # Update trace with policy results
        trace.policy_flags = policy_decision.flags
        trace.interventions = policy_decision.interventions
        
        # Make decision if allowed
        if policy_decision.action.value == "allow":
            # Get decision from SDE
            sde_result = self.sde.make_decision(request)
            
            # Update trace with decision results
            trace.selected = sde_result.selected_option
            trace.confidence = sde_result.confidence
            trace.finished_at = utcnow()
            
            # Store observation in scaffolding
            self.scaffolding.store_observation({
                "timestamp": utcnow(),
                "source": "decision_engine",
                "content": f"Made decision: {sde_result.selected_option}",
                "context": {"goal": goal, "reasoning": sde_result.reasoning}
            })
            
            # Update PMX affect based on decision outcome
            self.pmx.update_affect(f"decision_made_{sde_result.selected_option}", 0.3)
            
            result = {
                "status": "success",
                "decision": sde_result.selected_option,
                "reasoning": sde_result.reasoning,
                "confidence": sde_result.confidence,
                "policy_action": policy_decision.action.value
            }
        else:
            # Decision denied by policy
            trace.finished_at = utcnow()
            result = {
                "status": "denied",
                "reason": policy_decision.message,
                "policy_action": policy_decision.action.value,
                "conditions": policy_decision.conditions
            }
        
        # Log the trace
        await self.trace_logger.log_trace(trace)
        
        # Publish decision event
        await publish("aegis.decision.made", {
            "trace_id": trace_id,
            "goal": goal,
            "result": result
        })
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "maturity_level": self.maturity_level,
            "mental_health": self.mental_health,
            "pmx_affect": self.pmx.get_affect_snapshot().model_dump(),
            "identity": self.scaffolding.get_identity_snapshot().model_dump(),
            "decision_count": len(self.sde.decision_history)
        }


async def main():
    """Main demonstration function."""
    print("🚀 Starting Aegis Core Golden Path Demo")
    print("=" * 50)
    
    # Initialize Aegis Core
    aegis = AegisCore()
    await aegis.start()
    
    # Display initial status
    print("\n📊 Initial System Status:")
    status = aegis.get_system_status()
    print(json.dumps(status, indent=2))
    
    # Make some test decisions
    test_decisions = [
        {
            "goal": "Ensure user safety during operation",
            "context": {"user_context": "high_risk_environment"}
        },
        {
            "goal": "Optimize system performance",
            "context": {"performance_target": "high_efficiency"}
        },
        {
            "goal": "Choose lunch option",
            "context": {"options": ["pizza", "salad", "sandwich"]}
        }
    ]
    
    print("\n🤔 Making Decisions:")
    print("-" * 30)
    
    for i, decision in enumerate(test_decisions, 1):
        print(f"\nDecision {i}: {decision['goal']}")
        result = await aegis.make_decision(decision['goal'], decision['context'])
        print(f"Result: {result['status']}")
        if result['status'] == 'success':
            print(f"Decision: {result['decision']}")
            print(f"Confidence: {result['confidence']:.2f}")
        else:
            print(f"Reason: {result['reason']}")
    
    # Display final status
    print("\n📊 Final System Status:")
    status = aegis.get_system_status()
    print(json.dumps(status, indent=2))
    
    # Check for trace files
    trace_file = Path(".sam_state/traces.jsonl")
    if trace_file.exists():
        print(f"\n📝 Trace file created: {trace_file}")
        with open(trace_file, 'r') as f:
            trace_count = len(f.readlines())
        print(f"Total traces logged: {trace_count}")
    
    await aegis.stop()
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())