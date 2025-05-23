from final_chatbot import SupportChatBot

def test_chatbot():
    bot = SupportChatBot(company_data_file='company_data.json')  # make sure this JSON file is present and valid

    # Example query input dictionary
    input_data = {"query": "What are your working hours?"}

    # Get the bot response
    output = bot.process_query(input_data)

    print("Bot output:")
    print(output)

    # Basic checks
    assert "response" in output
    assert "emotion" in output
    assert "confidence" in output
    assert "session_id" in output
    assert "timestamp" in output

    print("Basic output keys check passed!")

if __name__ == "__main__":
    test_chatbot()
