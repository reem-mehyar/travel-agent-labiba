"""
Entry point for the AI Travel Agent application.
"""

from travel_agent import TravelAgent


def main() -> None:
    """
    Start the AI Travel Agent.
    """
    agent = TravelAgent()

    print("=" * 50)
    print("Labiba AI Travel Agent")
    print("Type 'exit' to quit.")
    print("=" * 50)

    while True:

        user_message = input("\nYou: ").strip()

        if user_message.lower() in ("exit", "quit"):
            print("\nGoodbye!")
            break

        if not user_message:
            continue

        try:
            response = agent.handle_request(user_message)
            print(f"\nLabiba: {response}")

        except Exception as error:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()