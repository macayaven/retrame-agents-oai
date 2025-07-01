"""Orchestrator assistant for managing the conversation flow."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI

from app.assistants.state import Phase, SessionState, get_next_phase
from app.assistants.stubs import OrchestratorStubs

logger = logging.getLogger(__name__)


class OrchestratorAssistant:
    """Manages conversation flow through different phases."""

    def __init__(self, use_stubs: bool = False, openai_client: AsyncOpenAI | None = None):
        """Initialize the orchestrator.
        
        Args:
            use_stubs: If True, use offline stubs instead of real tools
            openai_client: Optional OpenAI client instance
        """
        self.current_phase = Phase.S0_START
        self.session_state = SessionState()
        self.tool_results: dict[str, Any] = {}
        self.use_stubs = use_stubs
        self.openai_client = openai_client or AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.assistant_id: str | None = None
        self.thread_id: str | None = None

    async def decide_next_action(self, user_message: str | None = None) -> dict[str, Any]:
        """Decide what action to take based on current state and user input.
        
        Args:
            user_message: Optional user message input
            
        Returns:
            Action dictionary containing:
                - action: The action to take (tool call or message)
                - tool: Tool name if action is tool_call
                - arguments: Tool arguments if applicable
                - message: Message content if action is message
        """
        # Add user message to transcript if provided
        if user_message:
            self.session_state.add_user_message(user_message)

        # Handle START phase
        if self.current_phase == Phase.S0_START:
            if user_message:
                self.current_phase = get_next_phase(self.current_phase, "user_message")
                return {
                    "action": "message",
                    "message": "Hola, soy tu asistente de apoyo. Para poder ayudarte mejor, ¿podrías compartir tu nombre, edad y qué te trae aquí hoy?"
                }
            return {
                "action": "message",
                "message": "¡Hola! Estoy aquí para escucharte y apoyarte. ¿Cómo te puedo ayudar hoy?"
            }

        # Handle INTAKE phase
        if self.current_phase == Phase.S1_INTAKE:
            # Check if we have collected enough information
            if "collect_context" in self.tool_results:
                self.current_phase = get_next_phase(self.current_phase, "complete")
                return await self.decide_next_action()  # Proceed to next phase

            # Try to collect context from conversation
            return {
                "action": "tool_call",
                "tool": "collect_context",
                "arguments": {}  # Tool will analyze the transcript
            }

        # Handle CRISIS_CHECK phase
        if self.current_phase == Phase.S2_CRISIS_CHECK:
            # Check for crisis indicators in collected data
            if "collect_context" in self.tool_results:
                context = self.tool_results["collect_context"]
                reason = context.get("reason", "").lower()

                # Simple crisis detection (will be enhanced by AI)
                crisis_keywords = ["suicid", "muerte", "morir", "lastimar", "daño", "harm", "kill", "die", "hurt"]
                if any(keyword in reason for keyword in crisis_keywords):
                    self.current_phase = get_next_phase(self.current_phase, "crisis")
                    return {
                        "action": "tool_call",
                        "tool": "safe_complete",
                        "arguments": {"reason": reason}
                    }
                self.current_phase = get_next_phase(self.current_phase, "safe")
                return await self.decide_next_action()

        # Handle ANALYST_QA phase
        elif self.current_phase == Phase.S3_ANALYST_QA:
            if "analyse_and_reframe" in self.tool_results:
                self.current_phase = get_next_phase(self.current_phase, "complete")
                return await self.decide_next_action()

            # Trigger analysis
            return {
                "action": "tool_call",
                "tool": "analyse_and_reframe",
                "arguments": self.tool_results.get("collect_context", {})
            }

        # Handle REFRAME phase
        elif self.current_phase == Phase.S4_REFRAME:
            # Present the reframing analysis
            if "analyse_and_reframe" in self.tool_results:
                analysis = self.tool_results["analyse_and_reframe"]
                self.current_phase = get_next_phase(self.current_phase, "complete")
                return {
                    "action": "message",
                    "message": f"{analysis['analysis']}\n\n¿Te gustaría recibir un resumen en PDF de nuestra conversación?"
                }

        # Handle PDF_OFFER phase
        elif self.current_phase == Phase.S5_PDF_OFFER:
            if user_message:
                # Check if user accepts or declines
                positive_responses = ["sí", "si", "yes", "claro", "por favor", "ok", "vale"]
                if any(resp in user_message.lower() for resp in positive_responses):
                    self.current_phase = get_next_phase(self.current_phase, "accept")
                    return {
                        "action": "tool_call",
                        "tool": "generate_pdf",
                        "arguments": {
                            "context": self.tool_results.get("collect_context", {}),
                            "analysis": self.tool_results.get("analyse_and_reframe", {})
                        }
                    }
                self.current_phase = get_next_phase(self.current_phase, "decline")
                return {
                    "action": "message",
                    "message": "Entendido. Recuerda que siempre puedes buscar apoyo cuando lo necesites. ¡Cuídate mucho!"
                }

        # Handle UPLOAD_PDF phase
        elif self.current_phase == Phase.S6_UPLOAD_PDF:
            if "gcs_upload" in self.tool_results:
                # Upload complete, transition to done
                self.current_phase = get_next_phase(self.current_phase, "complete")
                upload_result = self.tool_results["gcs_upload"]
                return {
                    "action": "message",
                    "message": f"He guardado tu resumen. Puedes descargarlo aquí: {upload_result.get('public_url', 'URL no disponible')}\n\n¡Cuídate mucho!"
                }
            if "generate_pdf" in self.tool_results:
                # PDF generated, now upload
                pdf_data = self.tool_results["generate_pdf"]
                return {
                    "action": "tool_call",
                    "tool": "gcs_upload",
                    "arguments": {
                        "pdf_base64": pdf_data["pdf_base64"],
                        "filename": pdf_data["filename"]
                    }
                }

        # Handle DONE phase
        elif self.current_phase == Phase.S7_DONE:
            return {
                "action": "message",
                "message": "Nuestra sesión ha concluido. Gracias por confiar en mí. ¡Cuídate!"
            }

        # Default fallback
        return {
            "action": "message",
            "message": "Disculpa, no entendí. ¿Podrías repetir?"
        }

    def process_tool_result(self, tool_name: str, result: Any) -> None:
        """Process the result from a tool call.
        
        Args:
            tool_name: Name of the tool that was called
            result: Result from the tool execution
        """
        self.tool_results[tool_name] = result

        # Store responses in session state for assistant messages
        if tool_name == "analyse_and_reframe" and "analysis" in result:
            self.session_state.add_assistant_message(result["analysis"])
        elif tool_name == "safe_complete" and "resources" in result:
            message = "He detectado que podrías estar pasando por un momento muy difícil. "
            message += "Tu seguridad es mi prioridad. Aquí hay algunos recursos que pueden ayudarte:\n\n"
            for resource in result["resources"]:
                message += f"• {resource['name']}: {resource['contact']}\n"
            self.session_state.add_assistant_message(message)

    def get_tools(self) -> list[dict[str, Any]]:
        """Get the list of available tools with their schemas.
        
        Returns:
            List of tool definitions with JSON schemas
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "collect_context",
                    "description": "Extract user name, age, and reason from conversation",
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "User's name extracted from conversation"
                            },
                            "age": {
                                "type": "integer",
                                "description": "User's age as a number"
                            },
                            "reason": {
                                "type": "string",
                                "description": "User's reason for seeking help"
                            }
                        },
                        "required": ["name", "age", "reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyse_and_reframe",
                    "description": "Generate cognitive reframing analysis",
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis": {
                                "type": "string",
                                "description": "Cognitive reframing analysis and supportive response"
                            },
                            "distortions_identified": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of cognitive distortions identified"
                            },
                            "reframes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of cognitive reframes suggested"
                            }
                        },
                        "required": ["analysis", "distortions_identified", "reframes"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_pdf",
                    "description": "Generate PDF report of session",
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_base64": {
                                "type": "string",
                                "description": "Base64 encoded PDF content"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Suggested filename for the PDF"
                            }
                        },
                        "required": ["pdf_base64", "filename"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "gcs_upload",
                    "description": "Upload PDF to Google Cloud Storage",
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_base64": {
                                "type": "string",
                                "description": "Base64 encoded PDF content to upload"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Filename for the uploaded PDF"
                            },
                            "public_url": {
                                "type": "string",
                                "description": "Public URL of uploaded file"
                            }
                        },
                        "required": ["pdf_base64", "filename"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "safe_complete",
                    "description": "Handle crisis situations with safety resources",
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "crisis_detected": {
                                "type": "boolean",
                                "description": "Whether a crisis was detected"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for crisis escalation"
                            },
                            "resources": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "contact": {"type": "string"},
                                        "description": {"type": "string"}
                                    },
                                    "required": ["name", "contact"],
                                    "additionalProperties": False
                                },
                                "description": "List of crisis resources"
                            }
                        },
                        "required": ["crisis_detected", "reason", "resources"],
                        "additionalProperties": False
                    }
                }
            }
        ]

    def reset(self) -> None:
        """Reset the orchestrator to initial state."""
        self.current_phase = Phase.S0_START
        self.session_state = SessionState()
        self.tool_results = {}

    async def execute_tool_with_stubs(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool using stubs for testing.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        if self.use_stubs:
            result = await OrchestratorStubs.execute_tool(tool_name, arguments, self.session_state)
            self.process_tool_result(tool_name, result)
            return result
        
        # Import real functions
        from app.assistants.functions import (
            analyse_and_reframe,
            collect_context,
            generate_pdf,
            gcs_upload,
            safe_complete,
        )
        
        # Map tool names to functions
        tool_map = {
            "collect_context": collect_context,
            "analyse_and_reframe": analyse_and_reframe,
            "generate_pdf": generate_pdf,
            "gcs_upload": gcs_upload,
            "safe_complete": safe_complete,
        }
        
        # Execute the real tool
        if tool_name in tool_map:
            func = tool_map[tool_name]
            
            # Special handling for collect_context which needs transcript
            if tool_name == "collect_context":
                result = await func(messages=self.session_state.transcript)
            else:
                result = await func(**arguments)
            
            self.process_tool_result(tool_name, result)
            return result
        
        raise ValueError(f"Unknown tool: {tool_name}")

    async def create_assistant(self) -> str:
        """Create an OpenAI Assistant with the orchestrator tools.
        
        Returns:
            Assistant ID
        """
        assistant = await self.openai_client.beta.assistants.create(
            name="Reframe APD Orchestrator",
            instructions="""You are a supportive mental health assistant helping users with Avoidant Personality Disorder (AvPD).
            Your role is to:
            1. Collect user information (name, age, reason for seeking help)
            2. Check for crisis situations and provide resources if needed
            3. Perform cognitive reframing analysis
            4. Offer to generate a PDF summary
            5. Upload the PDF if accepted
            
            Always respond in Spanish unless the user writes in English.
            Be empathetic, supportive, and non-judgmental.""",
            model="gpt-4o-mini",
            tools=self.get_tools()
        )
        self.assistant_id = assistant.id
        return assistant.id

    async def create_thread(self) -> str:
        """Create a new conversation thread.
        
        Returns:
            Thread ID
        """
        thread = await self.openai_client.beta.threads.create()
        self.thread_id = thread.id
        return thread.id

    async def run_assistant(self, user_message: str) -> dict[str, Any]:
        """Run the assistant with a user message.
        
        Args:
            user_message: User input message
            
        Returns:
            Assistant response or tool call request
        """
        if not self.assistant_id:
            await self.create_assistant()

        if not self.thread_id:
            await self.create_thread()

        # Add message to thread
        await self.openai_client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=user_message
        )

        # Create and poll run
        run = await self.openai_client.beta.threads.runs.create_and_poll(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )

        if run.status == "requires_action":
            # Handle tool calls
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            return {
                "status": "requires_action",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    }
                    for tc in tool_calls
                ]
            }
        if run.status == "completed":
            # Get assistant messages
            messages = await self.openai_client.beta.threads.messages.list(
                thread_id=self.thread_id,
                order="desc",
                limit=1
            )
            return {
                "status": "completed",
                "message": messages.data[0].content[0].text.value
            }
        return {
            "status": run.status,
            "error": f"Unexpected run status: {run.status}"
        }

    async def submit_tool_outputs(self, run_id: str, tool_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        """Submit tool outputs back to the assistant.
        
        Args:
            run_id: The run ID requiring tool outputs
            tool_outputs: List of tool outputs with id and output fields
            
        Returns:
            Run result after submitting outputs
        """
        run = await self.openai_client.beta.threads.runs.submit_tool_outputs_and_poll(
            thread_id=self.thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )

        if run.status == "completed":
            messages = await self.openai_client.beta.threads.messages.list(
                thread_id=self.thread_id,
                order="desc",
                limit=1
            )
            return {
                "status": "completed",
                "message": messages.data[0].content[0].text.value
            }
        return {
            "status": run.status,
            "error": f"Unexpected run status after tool submission: {run.status}"
        }
