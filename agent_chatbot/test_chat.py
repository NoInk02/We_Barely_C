import json
import asyncio

# Assuming your chatbot class is named SupportChatBot and saved in chatbot.py
from chat_bot import SupportChatBot

# Load dummy tickets from a JSON file (adjust path as needed)
def load_dummy_tickets(path='sample_tickets.json'):
    with open(path, 'r') as f:
        return json.load(f)

async def main():
    print("Loading chatbot...")
    bot = SupportChatBot(company_data_file='company_data.json',ticket_data_file='sample_tickets.json')
    
    print("Chatbot ready! Type your questions below. Type 'exit' or 'quit' to stop.")
    
    while True:
        query = input("You: ").strip()
        if query.lower() in ['exit', 'quit']:
            print("Ending session. Goodbye!")
            session_summary = bot.end_session()
            print(f"Session Summary:\n{json.dumps(session_summary, indent=2)}")
            break

        # Process user query
        input_dict = {"query": query}
        response_data = bot.process_query(input_dict)

        if 'error' in response_data:
            print(f"Error: {response_data['error']}")
        else:
            print(f"Bot: {response_data['response']}\n")

if __name__ == "__main__":
    asyncio.run(main())
