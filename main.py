from agents.coder import run_coder


def main():
    print("Landing Page Builder")
    print("Type your instruction or 'exit' to quit.\n")

    while True:
        user_input = input("> ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        response = run_coder(user_input)
        print(f"\n{response}\n")


if __name__ == "__main__":
    main()
