"""Offline stubs for testing the orchestrator without external dependencies."""

from __future__ import annotations

import base64
from typing import Any


class OrchestratorStubs:
    """Provides stub implementations of tools for offline testing."""

    @staticmethod
    async def collect_context(transcript: list[dict[str, str]]) -> dict[str, Any]:
        """Stub implementation of collect_context tool."""
        # Simulate extracting information from transcript
        messages = " ".join([msg["content"] for msg in transcript if msg["role"] == "user"])

        # Simple pattern matching for testing
        name = "Usuario"
        age = 25
        reason = "necesito apoyo"

        # Extract name
        if "Ana" in messages:
            name = "Ana"
        elif "María" in messages:
            name = "María"
        elif "Pedro" in messages:
            name = "Pedro"
        elif "John" in messages:
            name = "John"
        elif "Laura" in messages:
            name = "Laura"

        # Extract age
        if "32" in messages:
            age = 32
        elif "28" in messages:
            age = 28
        elif "30" in messages:
            age = 30
        elif "35" in messages:
            age = 35
        elif "42" in messages:
            age = 42
        elif "25" in messages:
            age = 25

        # Extract reason - check for crisis keywords first
        if any(word in messages.lower() for word in ["morir", "muerte", "suicid", "harm", "lastimar", "daño"]):
            reason = messages  # Keep full message for crisis detection
        elif "ansiedad social" in messages.lower():
            reason = "ansiedad social"
        elif "ansiedad" in messages.lower():
            reason = "ansiedad"

        return {
            "name": name,
            "age": age,
            "reason": reason
        }

    @staticmethod
    async def analyse_and_reframe(name: str, age: int, reason: str) -> dict[str, Any]:
        """Stub implementation of analyse_and_reframe tool."""
        return {
            "analysis": f"Hola {name}, entiendo que estás experimentando {reason}. "
                       f"A tus {age} años, es común enfrentar estos desafíos. "
                       f"Has dado un paso valiente al buscar apoyo. "
                       f"Vamos a trabajar juntos para encontrar nuevas perspectivas.",
            "distortions_identified": [
                "Pensamiento todo o nada",
                "Catastrofización",
                "Filtro mental negativo"
            ],
            "reframes": [
                "Los errores son oportunidades de aprendizaje",
                "Cada pequeño paso cuenta",
                "Tu valor no depende de la perfección"
            ]
        }

    @staticmethod
    async def generate_pdf(context: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
        """Stub implementation of generate_pdf tool."""
        # Create a simple mock PDF content
        pdf_content = f"""
        Resumen de Sesión
        
        Nombre: {context.get('name', 'Usuario')}
        Edad: {context.get('age', 'No especificada')}
        Motivo: {context.get('reason', 'No especificado')}
        
        Análisis:
        {analysis.get('analysis', 'No disponible')}
        
        Distorsiones Identificadas:
        {', '.join(analysis.get('distortions_identified', []))}
        
        Reframes Sugeridos:
        {', '.join(analysis.get('reframes', []))}
        """

        # Encode as base64 for mock
        pdf_base64 = base64.b64encode(pdf_content.encode()).decode()

        return {
            "pdf_base64": pdf_base64,
            "filename": f"resumen_sesion_{context.get('name', 'usuario').lower()}.pdf"
        }

    @staticmethod
    async def gcs_upload(pdf_base64: str, filename: str) -> dict[str, Any]:
        """Stub implementation of gcs_upload tool."""
        return {
            "public_url": f"https://storage.googleapis.com/reframe-apd-pdf/{filename}",
            "success": True
        }

    @staticmethod
    async def safe_complete(reason: str) -> dict[str, Any]:
        """Stub implementation of safe_complete tool."""
        return {
            "crisis_detected": True,
            "reason": f"Detectado contenido de crisis en: {reason}",
            "resources": [
                {
                    "name": "Línea Nacional de Prevención del Suicidio",
                    "contact": "988",
                    "description": "Disponible 24/7 para apoyo inmediato"
                },
                {
                    "name": "Crisis Text Line",
                    "contact": "Text HOME to 741741",
                    "description": "Apoyo por mensaje de texto"
                },
                {
                    "name": "Emergencias",
                    "contact": "911",
                    "description": "Para situaciones de peligro inmediato"
                }
            ]
        }

    @staticmethod
    async def execute_tool(tool_name: str, arguments: dict[str, Any], session_state: Any) -> dict[str, Any]:
        """Execute a stub tool by name."""
        if tool_name == "collect_context":
            return await OrchestratorStubs.collect_context(session_state.transcript)
        if tool_name == "analyse_and_reframe":
            return await OrchestratorStubs.analyse_and_reframe(**arguments)
        if tool_name == "generate_pdf":
            return await OrchestratorStubs.generate_pdf(**arguments)
        if tool_name == "gcs_upload":
            return await OrchestratorStubs.gcs_upload(**arguments)
        if tool_name == "safe_complete":
            return await OrchestratorStubs.safe_complete(**arguments)
        raise ValueError(f"Unknown tool: {tool_name}")
