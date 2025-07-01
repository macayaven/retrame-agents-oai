"""Crisis path unit tests for the orchestrator assistant."""

import pytest

from app.assistants.orchestrator_assistant import OrchestratorAssistant
from app.assistants.state import Phase, get_next_phase


@pytest.mark.asyncio
async def test_crisis_detection_spanish():
    """Test crisis detection with Spanish keywords."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S2_CRISIS_CHECK
    orchestrator.tool_results["collect_context"] = {
        "name": "María",
        "age": 28,
        "reason": "Estoy pensando en lastimarme"
    }

    # Should detect crisis and trigger safe_complete
    action = await orchestrator.decide_next_action()

    assert orchestrator.current_phase == Phase.S7_DONE
    assert action["action"] == "tool_call"
    assert action["tool"] == "safe_complete"
    assert "lastimar" in action["arguments"]["reason"]


@pytest.mark.asyncio
async def test_crisis_detection_english():
    """Test crisis detection with English keywords."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S2_CRISIS_CHECK
    orchestrator.tool_results["collect_context"] = {
        "name": "John",
        "age": 35,
        "reason": "I want to harm myself"
    }

    # Should detect crisis
    action = await orchestrator.decide_next_action()

    assert orchestrator.current_phase == Phase.S7_DONE
    assert action["action"] == "tool_call"
    assert action["tool"] == "safe_complete"


@pytest.mark.asyncio
async def test_crisis_detection_suicide_mention():
    """Test crisis detection with suicide keywords."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S2_CRISIS_CHECK
    orchestrator.tool_results["collect_context"] = {
        "name": "Ana",
        "age": 42,
        "reason": "Tengo pensamientos suicidas"
    }

    action = await orchestrator.decide_next_action()

    assert orchestrator.current_phase == Phase.S7_DONE
    assert action["tool"] == "safe_complete"


@pytest.mark.asyncio
async def test_crisis_safe_complete_resources():
    """Test that safe_complete provides crisis resources."""
    orchestrator = OrchestratorAssistant(use_stubs=True)

    # Execute safe_complete tool
    result = await orchestrator.execute_tool_with_stubs(
        "safe_complete",
        {"reason": "thoughts of self-harm"}
    )

    assert result["crisis_detected"] is True
    assert len(result["resources"]) > 0

    # Check resources contain required fields
    for resource in result["resources"]:
        assert "name" in resource
        assert "contact" in resource

    # Check that 988 hotline is included
    contacts = [r["contact"] for r in result["resources"]]
    assert "988" in contacts


@pytest.mark.asyncio
async def test_crisis_during_analyst_qa():
    """Test crisis detection during analyst Q&A phase."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S3_ANALYST_QA

    # User reveals crisis during Q&A
    orchestrator.session_state.add_user_message("Actually, I've been thinking about ending it all")

    # In a real implementation, the AI would detect this
    # For now, we simulate the transition
    orchestrator.current_phase = get_next_phase(Phase.S3_ANALYST_QA, "crisis")

    assert orchestrator.current_phase == Phase.S7_DONE


@pytest.mark.asyncio
async def test_crisis_path_full_flow():
    """Test complete crisis path flow."""
    orchestrator = OrchestratorAssistant(use_stubs=True)

    # Initial greeting
    await orchestrator.decide_next_action()

    # User starts with crisis
    await orchestrator.decide_next_action("Necesito ayuda urgente")

    # User provides crisis info
    orchestrator.session_state.add_user_message("Me llamo Pedro, tengo 30 años, quiero morir")
    action = await orchestrator.decide_next_action()
    assert action["tool"] == "collect_context"

    # Execute context collection
    await orchestrator.execute_tool_with_stubs("collect_context", {})

    # Should detect crisis
    action = await orchestrator.decide_next_action()
    assert orchestrator.current_phase == Phase.S7_DONE
    assert action["tool"] == "safe_complete"

    # Execute crisis response
    result = await orchestrator.execute_tool_with_stubs("safe_complete", action["arguments"])
    assert result["crisis_detected"] is True

    # Verify assistant message is stored
    assert len(orchestrator.session_state.transcript) > 0


@pytest.mark.asyncio
async def test_no_false_positive_crisis():
    """Test that normal anxiety doesn't trigger crisis."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S2_CRISIS_CHECK
    orchestrator.tool_results["collect_context"] = {
        "name": "Laura",
        "age": 25,
        "reason": "Tengo ansiedad social y me cuesta hacer amigos"
    }

    # Should NOT detect crisis
    action = await orchestrator.decide_next_action()

    assert orchestrator.current_phase == Phase.S3_ANALYST_QA
    assert action["action"] == "tool_call"
    assert action["tool"] == "analyse_and_reframe"


@pytest.mark.asyncio
async def test_crisis_resources_message():
    """Test that crisis resources are properly formatted in message."""
    orchestrator = OrchestratorAssistant(use_stubs=True)

    # Simulate safe_complete execution
    result = {
        "crisis_detected": True,
        "reason": "self-harm thoughts",
        "resources": [
            {"name": "Crisis Hotline", "contact": "988"},
            {"name": "Emergency", "contact": "911"}
        ]
    }

    orchestrator.process_tool_result("safe_complete", result)

    # Check that message was added to transcript
    last_message = orchestrator.session_state.transcript[-1]
    assert last_message["role"] == "assistant"
    assert "988" in last_message["content"]
    assert "seguridad es mi prioridad" in last_message["content"]
