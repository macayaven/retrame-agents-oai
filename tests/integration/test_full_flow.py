import pytest

from app.assistants.__main__ import run_pipeline


@pytest.mark.asyncio
async def test_full_pipeline_offline():
    user_msgs = [
        "Hola, estoy aquí porque me da miedo hablar en público.",
        "Ayer durante la reunión de equipo con mi jefe pensé: \"Todos creen que soy incompetente\".",
        "Emoción principal: vergüenza 8/10.",
        "Por cierto, me llamo Ana y tengo 32 años.",
    ]

    result = await run_pipeline(user_msgs)
    assert "pdf_url" in result and result["pdf_url"].startswith("data:application/pdf;base64,")
    analysis = result["analysis"]
    assert analysis["certainty_before"] < analysis["certainty_after"]
