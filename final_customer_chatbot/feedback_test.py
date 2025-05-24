import google.generativeai as genai
from feedback import ChatFeedbackManager

# 1. Configure Gemini API Key (replace with your actual API key)
genai.configure(api_key="AIzaSyCSypgJaG3XLvlJvbDg_kg5RbzZm4vf9B8")

# 2. Create Gemini model client
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. Your session ID corresponding to your JSON file in chat_sessions/
session_id = "efd16659-089b-437a-abde-5c880a127eb0"

# 4. Instantiate manager
manager = ChatFeedbackManager(session_id=session_id, genai_client=model)

# 5. Run manager - will load session, generate summary, collect feedback, and save
manager.run()
