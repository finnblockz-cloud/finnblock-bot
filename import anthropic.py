import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
conversation = []

print("Chatbot ready. Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    conversation.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=conversation
    )

    reply = response.content[0].text
    conversation.append({"role": "assistant", "content": reply})
    print(f"\nClaude: {reply}\n")