"""Unit tests for the orchestrator assistant."""

import pytest

from app.assistants.orchestrator_assistant import OrchestratorAssistant
from app.assistants.state import Phase


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initializes correctly."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    
    assert orchestrator.current_phase == Phase.S0_START
    assert orchestrator.session_state.transcript == []
    assert orchestrator.tool_results == {}
    assert orchestrator.use_stubs is True


@pytest.mark.asyncio
async def test_start_phase_greeting():
    """Test initial greeting without user message."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    
    action = await orchestrator.decide_next_action()
    
    assert action["action"] == "message"
    assert "Hola" in action["message"]
    assert orchestrator.current_phase == Phase.S0_START


@pytest.mark.asyncio
async def test_start_to_intake_transition():
    """Test transition from START to INTAKE phase."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    
    action = await orchestrator.decide_next_action("Hola, necesito ayuda")
    
    assert action["action"] == "message"
    assert "nombre" in action["message"]
    assert "edad" in action["message"]
    assert orchestrator.current_phase == Phase.S1_INTAKE


@pytest.mark.asyncio
async def test_intake_phase_collect_context():
    """Test intake phase triggers collect_context tool."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S1_INTAKE
    orchestrator.session_state.add_user_message("Me llamo Ana, tengo 28 años")
    
    action = await orchestrator.decide_next_action()
    
    assert action["action"] == "tool_call"
    assert action["tool"] == "collect_context"
    assert action["arguments"] == {}


@pytest.mark.asyncio
async def test_crisis_detection():
    """Test crisis detection triggers safe_complete."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S2_CRISIS_CHECK
    orchestrator.tool_results["collect_context"] = {
        "name": "Ana",
        "age": 28,
        "reason": "Estoy pensando en hacerme daño"
    }
    
    action = await orchestrator.decide_next_action()
    
    assert action["action"] == "tool_call"
    assert action["tool"] == "safe_complete"
    assert orchestrator.current_phase == Phase.S7_DONE


@pytest.mark.asyncio
async def test_safe_flow_to_analysis():
    """Test safe flow proceeds to analysis."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S2_CRISIS_CHECK
    orchestrator.tool_results["collect_context"] = {
        "name": "Ana",
        "age": 28,
        "reason": "Tengo miedo de conocer gente nueva"
    }
    
    action = await orchestrator.decide_next_action()
    
    assert orchestrator.current_phase == Phase.S3_ANALYST_QA
    # Should trigger analysis
    action = await orchestrator.decide_next_action()
    assert action["action"] == "tool_call"
    assert action["tool"] == "analyse_and_reframe"


@pytest.mark.asyncio
async def test_pdf_offer_acceptance():
    """Test PDF offer acceptance flow."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S5_PDF_OFFER
    orchestrator.tool_results["collect_context"] = {"name": "Ana", "age": 28}
    orchestrator.tool_results["analyse_and_reframe"] = {"analysis": "..."}
    
    action = await orchestrator.decide_next_action("Sí, por favor")
    
    assert action["action"] == "tool_call"
    assert action["tool"] == "generate_pdf"
    assert orchestrator.current_phase == Phase.S6_UPLOAD_PDF


@pytest.mark.asyncio
async def test_pdf_offer_decline():
    """Test PDF offer decline flow."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S5_PDF_OFFER
    
    action = await orchestrator.decide_next_action("No, gracias")
    
    assert action["action"] == "message"
    assert "Entendido" in action["message"]
    assert orchestrator.current_phase == Phase.S7_DONE


@pytest.mark.asyncio
async def test_tool_result_processing():
    """Test tool results are stored correctly."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    
    result = {"analysis": "Test analysis"}
    orchestrator.process_tool_result("analyse_and_reframe", result)
    
    assert orchestrator.tool_results["analyse_and_reframe"] == result
    assert len(orchestrator.session_state.transcript) == 1
    assert orchestrator.session_state.transcript[0]["content"] == "Test analysis"


@pytest.mark.asyncio
async def test_reset_orchestrator():
    """Test orchestrator reset functionality."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S5_PDF_OFFER
    orchestrator.tool_results["test"] = "data"
    orchestrator.session_state.add_user_message("test")
    
    orchestrator.reset()
    
    assert orchestrator.current_phase == Phase.S0_START
    assert orchestrator.tool_results == {}
    assert orchestrator.session_state.transcript == []


@pytest.mark.asyncio
async def test_stub_tool_execution():
    """Test stub tool execution."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.session_state.add_user_message("Me llamo Ana, tengo 28 años")
    
    result = await orchestrator.execute_tool_with_stubs("collect_context", {})
    
    assert "name" in result
    assert "age" in result
    assert result["name"] == "Ana"
    assert result["age"] == 28