#!/usr/bin/env python3
"""CLI demo harness for the orchestrator assistant."""

import asyncio
import os
import sys

from app.assistants.orchestrator_assistant import OrchestratorAssistant


async def run_demo(use_stubs: bool = True):
    """Run the orchestrator demo in REPL mode.

    Args:
        use_stubs: If True, use offline stubs (default). If False, use real OpenAI.
    """
    print("🤖 Reframe APD Orchestrator Demo")
    print("=" * 50)
    print(f"Mode: {'Offline (Stubs)' if use_stubs else 'Online (OpenAI)'}")
    print("Type 'exit' or 'quit' to end the session")
    print("=" * 50)
    print()

    # Initialize orchestrator
    orchestrator = OrchestratorAssistant(use_stubs=use_stubs)

    # Initial greeting
    action = await orchestrator.decide_next_action()
    if action["action"] == "message":
        print(f"Assistant: {action['message']}")
        print()

    # Main conversation loop
    while orchestrator.current_phase.value != "done":
        # Get user input
        user_input = input("You: ").strip()

        if user_input.lower() in ['exit', 'quit']:
            print("\nExiting demo...")
            break

        # Process user message
        action = await orchestrator.decide_next_action(user_input)

        # Handle actions
        while action["action"] == "tool_call":
            tool_name = action["tool"]
            arguments = action["arguments"]

            print(f"\n[Calling tool: {tool_name}]")

            # Execute tool
            if use_stubs:
                result = await orchestrator.execute_tool_with_stubs(tool_name, arguments)
                print(f"[Tool result: {list(result.keys())}]")
            else:
                # In real mode, would use OpenAI assistant
                print("[Tool execution would happen via OpenAI]")
                break

            # Get next action
            action = await orchestrator.decide_next_action()

        # Display message
        if action["action"] == "message":
            print(f"\nAssistant: {action['message']}")
            print()

    print("\n✅ Demo session completed!")


async def main():
    """Main entry point for the demo."""
    # Check if running in offline mode
    offline_mode = os.getenv("OFFLINE", "1") == "1"

    if not offline_mode and not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set and OFFLINE=0")
        print("Either set OFFLINE=1 or provide OPENAI_API_KEY")
        sys.exit(1)

    await run_demo(use_stubs=offline_mode)


if __name__ == "__main__":
    asyncio.run(main())
