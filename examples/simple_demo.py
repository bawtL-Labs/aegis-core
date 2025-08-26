#!/usr/bin/env python3
"""
Simple Demo - Basic Aegis Core functionality without async features.

This demonstrates the core functionality without the complexity of async operations.
"""

import sys
sys.path.insert(0, 'src')

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from sam_core import (
    LocalJSONLStore,
    TraceLogger,
    SelfGovernancePolicy,
    DecisionTrace,
    DecodingMode,
    generate_trace_id,
    utcnow,
    PolicyAction
)

from sam_core.contracts.pmx import PMXInterface, AffectSnapshot, Traits
from sam_core.contracts.scaffolding import ScaffoldingInterface, IdentitySnapshot
from sam_core.contracts.sde import SDEInterface, DecisionRequestView, DecisionOutcomeView


class MockTraits:
    """Mock traits implementation."""
    
    def __init__(self):
        self.creative = 0.7
        self.analytical = 0.8
        self.empathic = 0.9
        self.curiosity = 0.6
        self.balance = 0.5


class MockAffectSnapshot:
    """Mock affect snapshot implementation."""
    
    def __init__(self):
        self.joy = 0.6
        self.fear = 0.1
        self.sadness = 0.0
        self.anger = 0.0
        self.surprise = 0.2
        self.disgust = 0.0
    
    def as_dict(self) -> Dict[str, Any]:
        return {
            "joy": self.joy,
            "fear": self.fear,
            "sadness": self.sadness,
            "anger": self.anger,
            "surprise": self.surprise,
            "disgust": self.disgust
        }


class MockPMX(PMXInterface):
    """Mock PMX implementation for demonstration."""
    
    def __init__(self):
        self.traits = MockTraits()
        self.affect = MockAffectSnapshot()
    
    def get_traits(self) -> Traits:
        return self.traits
    
    def get_affect_snapshot(self) -> AffectSnapshot:
        return self.affect
    
    def update_affect(self, stimulus: str, intensity: float) -> AffectSnapshot:
        if "positive" in stimulus.lower():
            self.affect.joy = min(1.0, self.affect.joy + intensity * 0.1)
        elif "negative" in stimulus.lower():
            self.affect.fear = min(1.0, self.affect.fear + intensity * 0.1)
        return self.affect
    
    def get_boundary_manager(self):
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
        relevant = []
        for memory in self.memories[-limit:]:
            if any(word in memory.content.lower() for word in query.lower().split()):
                relevant.append(memory)
        return relevant
    
    def create_plan(self, goal: str, context: dict) -> str:
        plan_id = f"plan_{len(self.plans)}"
        return plan_id
    
    def update_plan(self, plan_id: str, updates: dict) -> None:
        pass
    
    def get_plan_summary(self, plan_id: str):
        return None
    
    def get_active_plans(self):
        return []
    
    def get_identity_snapshot(self) -> IdentitySnapshot:
        return self.identity
    
    def update_identity(self, updates: dict) -> None:
        pass


class MockSDE(SDEInterface):
    """Mock SDE implementation for demonstration."""
    
    def __init__(self):
        self.decision_history = []
    
    def make_decision(self, request: DecisionRequestView) -> DecisionOutcomeView:
        if "safety" in request.goal.lower():
            selected_option = "prioritize_safety"
            confidence = 0.9
        elif "efficiency" in request.goal.lower():
            selected_option = "optimize_performance"
            confidence = 0.8
        else:
            selected_option = "balanced_approach"
            confidence = 0.7
        
        result = DecisionOutcomeView(
            request_id=request.request_id,
            selected_option=selected_option,
            reasoning=f"Selected {selected_option} based on goal analysis",
            confidence=confidence,
            execution_plan={"steps": ["analyze", "execute", "monitor"]}
        )
        
        self.decision_history.append(result)
        return result
    
    def get_decision_options(self, request: DecisionRequestView):
        return []
    
    def evaluate_option(self, option_id: str, context: dict) -> dict:
        return {"utility": 0.5, "risks": [], "requirements": []}
    
    def get_decision_history(self, limit: int = 100) -> List[DecisionOutcomeView]:
        return self.decision_history[-limit:]
    
    def update_decision_model(self, feedback: dict) -> None:
        pass


class SimpleAegisCore:
    """Simplified Aegis Core without async features."""
    
    def __init__(self, state_path: str = ".sam_state"):
        # Initialize core components
        self.state_store = LocalJSONLStore(state_path)
        self.trace_logger = TraceLogger(self.state_store, "traces/decisions")
        self.policy = SelfGovernancePolicy()
        
        # Initialize external components
        self.pmx = MockPMX()
        self.scaffolding = MockScaffolding()
        self.sde = MockSDE()
        
        # State
        self.maturity_level = 6
        self.mental_health = 0.85
    
    def make_decision(self, goal: str, context: dict = None) -> dict:
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
        request = DecisionRequestView(
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
            constraints={"constraints": identity.constraints},
            compute_budget=request.compute_budget,
            time_budget_ms=request.time_budget_ms,
            maturity_level=self.maturity_level,
            mental_health=self.mental_health,
            pmx_affect=pmx_affect_snapshot.as_dict(),
            decoding_mode=DecodingMode.REASONING,
            confidence=0.8
        )
        
        # Apply policy review
        policy_decision = self.policy.review(trace)
        
        # Update trace with policy results
        trace.policy_flags = policy_decision.flags
        trace.interventions = policy_decision.conditions
        
        # Make decision if allowed
        if policy_decision.action == PolicyAction.ALLOW:
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
                "reason": f"Policy {policy_decision.action.value}",
                "policy_action": policy_decision.action.value,
                "conditions": policy_decision.conditions
            }
        
        # Log the trace (synchronous)
        self.trace_logger._log_trace_sync(trace)
        
        return result
    
    def get_system_status(self) -> dict:
        """Get current system status."""
        return {
            "maturity_level": self.maturity_level,
            "mental_health": self.mental_health,
            "pmx_affect": self.pmx.get_affect_snapshot().as_dict(),
            "identity": self.scaffolding.get_identity_snapshot().model_dump(),
            "decision_count": len(self.sde.decision_history)
        }


def main():
    """Main demonstration function."""
    print("🚀 Starting Aegis Core Simple Demo")
    print("=" * 50)
    
    # Initialize Aegis Core
    aegis = SimpleAegisCore()
    
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
        result = aegis.make_decision(decision['goal'], decision['context'])
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
    trace_file = Path(".sam_state/traces/decisions.jsonl")
    if trace_file.exists():
        print(f"\n📝 Trace file created: {trace_file}")
        with open(trace_file, 'r') as f:
            trace_count = len(f.readlines())
        print(f"Total traces logged: {trace_count}")
    
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    main()