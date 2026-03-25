import asyncio
from main import agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

APP_NAME = "google-calendar-agent"
USER_ID = "user-1"
SESSION_ID = "cli-session"

async def interactive_chat():
    session_service = InMemorySessionService()

    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service
    )

    # ✅ Create session ONCE
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    print("Google Calendar Agent (Runner CLI)")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("user: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        try:
            content = types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )

            events = runner.run(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=content
            )

            final_response = ""
            for event in events:
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_response += part.text

            print("agent:", final_response.strip())

        except Exception as e:
            print("agent: Error -", e)


if __name__ == "__main__":
    asyncio.run(interactive_chat())