from final_chatbot import SupportChatBot

def test_chatbot():
    bot = SupportChatBot()
    print("💬 Chatbot is running. Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "quit":
            print("\n👋 Ending session...")
            break
        
        input_data = {"query": user_input}
        output = bot.process_query(input_data)
        print("Bot:", output)

    # Call end_session to save the chat session
    session_data = bot.end_session()
    print("\n✅ Session saved! Details:")
    print(session_data)

if __name__ == "__main__":
    test_chatbot()
