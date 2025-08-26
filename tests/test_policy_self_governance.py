"""Tests for SelfGovernancePolicy functionality."""

import pytest
from datetime import datetime

from sam_core.policy.self_governance import (
    SelfGovernancePolicy, 
    MaturityGatePolicy, 
    MentalHealthPolicy, 
    PMXBoundaryPolicy
)
from sam_core.policy.types import PolicyAction
from sam_core.tracing.models import DecisionTrace, DecodingMode, PolicyFlag
from sam_core.common.ids import generate_trace_id


class TestMaturityGatePolicy:
    """Test MaturityGatePolicy functionality."""
    
    @pytest.fixture
    def policy(self):
        """Create a MaturityGatePolicy instance."""
        return MaturityGatePolicy({
            "safety_critical": 8,
            "financial": 7,
            "personal_data": 6,
            "system_access": 9,
            "general": 3
        })
    
    def test_safety_critical_decision_denied(self, policy):
        """Test that safety critical decisions require high maturity."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Prevent harm to user",
            maturity_level=5,  # Below required 8
            mental_health=0.8,
            pmx_affect={"fear": 0.3},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.DENY
        assert PolicyFlag.MATURITY_GATE in decision.flags
        assert "maturity level 8" in decision.message
    
    def test_financial_decision_allowed(self, policy):
        """Test that financial decisions are allowed with sufficient maturity."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Invest money in stocks",
            maturity_level=8,  # Above required 7
            mental_health=0.8,
            pmx_affect={"joy": 0.6},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.ALLOW
        assert len(decision.flags) == 0
    
    def test_decision_classification(self, policy):
        """Test decision type classification."""
        # Test safety critical
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Assess safety risk",
            maturity_level=5,
            mental_health=0.8,
            pmx_affect={},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        decision = policy.review(trace)
        assert decision.action == PolicyAction.DENY
        
        # Test financial
        trace.goal = "Make financial investment"
        decision = policy.review(trace)
        assert decision.action == PolicyAction.DENY  # Still denied due to maturity
        
        # Test general
        trace.goal = "Choose lunch option"
        decision = policy.review(trace)
        assert decision.action == PolicyAction.ALLOW  # Allowed for general decisions


class TestMentalHealthPolicy:
    """Test MentalHealthPolicy functionality."""
    
    @pytest.fixture
    def policy(self):
        """Create a MentalHealthPolicy instance."""
        return MentalHealthPolicy(risk_threshold=0.4, critical_threshold=0.2)
    
    def test_critical_mental_health_denied(self, policy):
        """Test that critical mental health leads to denial."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Make important decision",
            maturity_level=8,
            mental_health=0.1,  # Below critical threshold
            pmx_affect={"sadness": 0.8},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.DENY
        assert PolicyFlag.MENTAL_HEALTH_RISK in decision.flags
        assert "critical" in decision.message.lower()
    
    def test_risk_mental_health_warning(self, policy):
        """Test that risk mental health leads to warning."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Make important decision",
            maturity_level=8,
            mental_health=0.3,  # Below risk threshold but above critical
            pmx_affect={"fear": 0.6},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.WARN
        assert PolicyFlag.MENTAL_HEALTH_RISK in decision.flags
        assert "risk" in decision.message.lower()
    
    def test_good_mental_health_allowed(self, policy):
        """Test that good mental health is allowed."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Make important decision",
            maturity_level=8,
            mental_health=0.8,  # Above risk threshold
            pmx_affect={"joy": 0.7},
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.ALLOW
        assert len(decision.flags) == 0


class TestPMXBoundaryPolicy:
    """Test PMXBoundaryPolicy functionality."""
    
    @pytest.fixture
    def policy(self):
        """Create a PMXBoundaryPolicy instance."""
        return PMXBoundaryPolicy({
            "anger": 0.8,
            "fear": 0.7,
            "sadness": 0.8,
            "joy": 0.9,
            "surprise": 0.9,
            "disgust": 0.8
        })
    
    def test_boundary_violation_conditioned(self, policy):
        """Test that boundary violations lead to conditions."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Make important decision",
            maturity_level=8,
            mental_health=0.8,
            pmx_affect={"anger": 0.9, "fear": 0.8},  # Both exceed limits
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.CONDITION
        assert PolicyFlag.PMX_BOUNDARY in decision.flags
        assert "boundary violations" in decision.message.lower()
        assert decision.conditions is not None
        assert decision.conditions["pmx_boundary_check"] is True
    
    def test_within_boundaries_allowed(self, policy):
        """Test that decisions within boundaries are allowed."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Make important decision",
            maturity_level=8,
            mental_health=0.8,
            pmx_affect={"joy": 0.6, "fear": 0.3},  # Within limits
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.ALLOW
        assert len(decision.flags) == 0


class TestSelfGovernancePolicy:
    """Test SelfGovernancePolicy integration."""
    
    @pytest.fixture
    def policy(self):
        """Create a SelfGovernancePolicy instance."""
        return SelfGovernancePolicy()
    
    def test_complex_decision_denied(self, policy):
        """Test that complex decisions with multiple issues are denied."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Access system root privileges",  # System access requires maturity 9
            maturity_level=5,  # Below required level
            mental_health=0.1,  # Critical mental health
            pmx_affect={"anger": 0.9},  # Boundary violation
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        # Should be denied due to maturity gate (first in chain)
        assert decision.action == PolicyAction.DENY
        assert PolicyFlag.MATURITY_GATE in decision.flags
    
    def test_safe_decision_allowed(self, policy):
        """Test that safe decisions are allowed."""
        trace = DecisionTrace(
            trace_id=generate_trace_id(),
            started_at=datetime.now(),
            goal="Choose lunch option",  # General decision
            maturity_level=8,  # High maturity
            mental_health=0.9,  # Good mental health
            pmx_affect={"joy": 0.6},  # Within boundaries
            decoding_mode=DecodingMode.REASONING,
            confidence=0.9
        )
        
        decision = policy.review(trace)
        
        assert decision.action == PolicyAction.ALLOW
        assert len(decision.flags) == 0