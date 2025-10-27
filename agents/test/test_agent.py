"""
Test Agent Functionality

Tests the LangChain agent's ability to answer questions about DBT data
using MCP tools.
"""

from agents.agent import ask_agent


def test_agent():
    """
    Test the agent with various questions about DBT data

    Tests cover:
    - Listing all models
    - Searching for specific models
    - Getting model details
    """
    print("\n" + "🧪 Starting Agent Tests..." + "\n")

    # Define test questions in English
    test_questions = [
        "What tables do we have?",
        "Are there any order-related tables?",
        "Please describe the structure of the dim_customers table"
    ]

    # Test each question
    for i, question in enumerate(test_questions, 1):
        print("=" * 50)
        print(f"\nQuestion {i}: {question}\n")
        print("-" * 50)

        try:
            # Ask the agent
            answer = ask_agent(question)

            # Print the answer
            print(f"\nAnswer:\n{answer}\n")

        except KeyboardInterrupt:
            print("\n\n❌ Tests interrupted by user\n")
            break

        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__} - {str(e)}\n")

        print()  # Empty line between questions

    print("=" * 50)
    print("\n✅ Tests Completed\n")


def test_agent_interactive():
    """
    Interactive mode - ask questions interactively

    Allows users to ask multiple questions in a loop until they type 'quit'.
    """
    print("\n" + "=" * 80)
    print("  DBT Data Discovery Agent - Interactive Mode")
    print("=" * 80)
    print("\nType 'quit' or 'exit' to exit\n")

    while True:
        try:
            # Get user input
            question = input("❓ Question: ").strip()

            # Check for exit commands
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            # Skip empty questions
            if not question:
                continue

            # Ask the agent
            print("\nThinking...\n")
            answer = ask_agent(question)

            # Print the answer
            print(f"💡 Answer:\n{answer}\n")
            print("-" * 80 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break

        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__} - {str(e)}\n")
            print("-" * 80 + "\n")


def test_specific_questions():
    """
    Test specific advanced questions

    Tests more complex queries and edge cases.
    """
    print("\n" + "🧪 Testing Advanced Questions..." + "\n")

    advanced_questions = [
        "List all dimension tables",
        "What fact tables do we have?",
        "Tell me about tables related to customer data",
        "Which tables contain order information?",
        "I want to understand the mart_sales_overview table"
    ]

    for i, question in enumerate(advanced_questions, 1):
        print("=" * 50)
        print(f"\nAdvanced Question {i}: {question}\n")
        print("-" * 50)

        try:
            answer = ask_agent(question)
            print(f"\nAnswer:\n{answer}\n")

        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__} - {str(e)}\n")

        print()

    print("=" * 50)
    print("\n✅ Advanced Tests Completed\n")


if __name__ == "__main__":
    """
    Run agent tests

    Usage:
        python -m agents.test.test_agent              # Run basic tests
        python -m agents.test.test_agent --interactive # Interactive mode
        python -m agents.test.test_agent --advanced    # Advanced tests
    """
    import sys

    # Check for command-line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode in ['--interactive', '-i']:
            test_agent_interactive()
        elif mode in ['--advanced', '-a']:
            test_specific_questions()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage:")
            print("  python -m agents.test.test_agent              # Basic tests")
            print("  python -m agents.test.test_agent --interactive # Interactive mode")
            print("  python -m agents.test.test_agent --advanced    # Advanced tests")
    else:
        # Run basic tests
        test_agent()
