from agents.agent3_analytics import run_agent3
from agents.agent1_creative import run_agent1
from agents.agent2_designer import run_agent2
from agents.agent4_reporter import run_agent4
from agents.agent5_publisher import run_agent5


def confirm(message):
    while True:
        answer = input(f"\n{message} (yes/no): ").strip().lower()
        if answer in ["yes", "y"]:
            return True
        elif answer in ["no", "n"]:
            return False
        else:
            print("Please type yes or no.")


def main():
    print("=" * 50)
    print("BeyoondBoundariess — AI Agent System")
    print("=" * 50)

    # Agent 3 always runs first — no confirmation needed
    run_agent3()

    # Agent 1 — Creative Head
    if confirm("Run Agent 1 — Creative Head (content ideas)?"):
        run_agent1()
    else:
        print("Agent 1 skipped.")

    # Agent 2 — Visual Designer
    if confirm("Run Agent 2 — Visual Designer (thumbnail concepts)?"):
        run_agent2()
    else:
        print("Agent 2 skipped.")

    # Agent 4 — Executive Reporter
    if confirm("Run Agent 4 — Executive Reporter (send weekly email)?"):
        run_agent4()
    else:
        print("Agent 4 skipped.")

    # Agent 5 — Auto Publisher
    if confirm("Run Agent 5 — Auto Publisher (upload to YouTube)?"):
        run_agent5()
    else:
        print("Agent 5 skipped.")

    print("\n" + "=" * 50)
    print("All done! BeyoondBoundariess agents completed.")
    print("=" * 50)


if __name__ == "__main__":
    main()