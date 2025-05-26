import json
from datetime import datetime
from  config.config import settings
import google.generativeai as genai


class ChatFeedbackManager:
    def __init__(self, session_data):
        self.session_data = session_data

        # 1. Configure Gemini API Key (replace with your actual API key)
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # 2. Create Gemini model client

        model = genai.GenerativeModel('gemini-1.5-flash')

        self.genai = model # Gemini or LLM client

    def generate_summary_with_genai(self):
        history_text = ""
        for turn in self.session_data["history"]:
            user = turn["input"]
            bot = turn["response"]
            emotion = turn["emotion"]["label"]
            confidence = turn["confidence"]
            history_text += f"User: {user}\nBot: {bot.strip()}\nEmotion: {emotion}, Confidence: {confidence:.2f}\n\n"

        prompt = f"""Summarize the following chat session between a user and an AI agent in a paragraph. Describe the user's tone, emotional state, the AI's responses, and the overall flow of the conversation.

    Chat History:
    {history_text}

    Summary:"""

        response = self.genai.generate_content(prompt).text
        return response.strip()


    def collect_feedback(self):
        print("\n=== Feedback Time ===")
        summary = self.generate_summary_with_genai()

        try:
            rating_input = ""
            if rating_input == "":
                print("No manual rating provided, using auto-feedback comment...")
                return self.generate_auto_feedback(summary)

            rating = int(rating_input)
            if rating < 1 or rating > 5:
                print("Invalid rating, using auto-feedback comment...")
                return self.generate_auto_feedback(summary)

            comments = ""
            return {
                "rating": rating,
                "comments": comments,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }

        except Exception:
            print("Error in manual feedback input, using auto-feedback comment...")
            return self.generate_auto_feedback(summary)

    def generate_auto_feedback(self, summary):
        prompt = f"""Based on the following user-AI chat session summary, write a brief feedback comment (1-2 lines). Do not include a rating.

    Session Summary:
    {summary}

    Comments:"""

        response = self.genai.generate_content(prompt).text
        return {
            "rating": 3,
            "comments": response.strip(),
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }

    def parse_feedback_response(self, text):
        try:
            lines = text.strip().splitlines()
            rating = int(lines[0].split(":")[1].strip())
            comment = lines[1].split(":", 1)[1].strip()
            return {
                "rating": rating,
                "comments": comment,
                "timestamp": datetime.now().isoformat()
            }
        except Exception:
            return {
                "rating": 3,
                "comments": "Default feedback due to parsing error.",
                "timestamp": datetime.now().isoformat()
            }


    def run(self):
        if not self.session_data:
            print("❌ No session data to process.")
            return
        feedback = self.collect_feedback()
        return feedback
