import json
from statistics import mean
import google.generativeai as genai
from datetime import datetime
import os

class CSATAnalyzer:
    def __init__(self, session_json_path, api_key):
        self.session_json_path = session_json_path
        self.session_data = self.load_json(session_json_path)
        self.feedback_data = self.load_json(self.get_feedback_path())
        self.scores = self.extract_scores()

        # Initialize Gemini (Google Generative AI)
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel("gemini-1.5-flash")

    def get_feedback_path(self):
        filename = os.path.basename(self.session_json_path)  # session_...
        # Go one level above chat_sessions folder to final_customer_chatbot folder
        parent_dir = os.path.dirname(os.path.dirname(self.session_json_path))
        return os.path.join(parent_dir, filename.replace('session_', 'feedback_'))


    def load_json(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[WARNING] File not found: {path}")
            return {}

    def extract_scores(self):
        scores = [t.get('csat_score') for t in self.session_data.get('history', []) if t.get('csat_score') is not None]
        if self.feedback_data:
            feedback_rating = self.feedback_data.get('feedback', {}).get('rating')
            if feedback_rating is not None:
                scores.append(feedback_rating)
        return scores

    def compute_summary(self):
        summary = {
            "average_score": None,
            "total_ratings": len(self.scores),
            "low_score_count": len([s for s in self.scores if s <= 3]),
            "average_handling_time": None,
            "average_confidence": None,
            "emotion_distribution": {}
        }

        if self.scores:
            summary["average_score"] = round(mean(self.scores), 2)

        if 'duration_seconds' in self.session_data:
            summary['average_handling_time'] = round(self.session_data['duration_seconds'], 2)

        confidences = [t.get('confidence') for t in self.session_data.get('history', []) if 'confidence' in t]
        if confidences:
            summary['average_confidence'] = round(mean(confidences), 2)

        emotions = [t.get('emotion', {}).get('label') for t in self.session_data.get('history', [])]
        for e in emotions:
            if e:
                summary['emotion_distribution'][e] = summary['emotion_distribution'].get(e, 0) + 1

        return summary

    def ask_llm_for_improvement(self):
        summary = self.compute_summary()
        prompt = f"""
        Chatbot Performance Summary:
        - Average CSAT Score: {summary['average_score']}
        - Total Ratings: {summary['total_ratings']}
        - Low Ratings (≤3): {summary['low_score_count']}
        - Average Handling Time (seconds): {summary['average_handling_time']}
        - Average Confidence: {summary['average_confidence']}
        - Emotion Distribution: {summary['emotion_distribution']}

        Based on this performance summary, identify:
        1. Key areas for improvement (e.g., empathy, clarity, speed, escalation).
        2. Specific, actionable recommendations for the chatbot to improve user experience.
        3. Patterns in emotion and confidence levels that could explain low ratings.
        4. Be conscise, we dont need big paragraphs.
        Provide clear and concise feedback.
        """
        response = self.llm.generate_content(prompt)
        return response.text.strip()

    def run(self):
        print(f"\n📊 Analyzing Session: {os.path.basename(self.session_json_path)}")
        summary = self.compute_summary()
        print("CSAT Summary:", json.dumps(summary, indent=2))

        suggestions = self.ask_llm_for_improvement()
        print("\n💡 Suggestions for Improvement:\n")
        print(suggestions)

    # 💾 Save analysis and suggestions to a file (INSIDE the method)
        output_file = self.session_json_path.replace('.json', '_analysis.json')
        with open(output_file, 'w') as f:
            json.dump({
                "summary": summary,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        print(f"\n✅ Analysis saved to {output_file}")


    @staticmethod
    def run_folder_analysis(folder_path, api_key):
        print(f"\n🔍 Analyzing all sessions in folder: {folder_path}\n")
        for filename in os.listdir(folder_path):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_path = os.path.join(folder_path, filename)
                analyzer = CSATAnalyzer(session_path, api_key)
                analyzer.run()
                print("\n" + "="*50 + "\n")

# Example Usage
if __name__ == "__main__":
    API_KEY = "AIzaSyCSypgJaG3XLvlJvbDg_kg5RbzZm4vf9B8"
    folder = "chat_sessions"
    CSATAnalyzer.run_folder_analysis(folder, API_KEY)
