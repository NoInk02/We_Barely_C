import json
from statistics import mean
import google.generativeai as genai

class CSATAnalyzer:
    def __init__(self, session_json_path):
        self.session_json_path = session_json_path
        self.session_data = self.load_session()
        self.scores = self.extract_scores()
        self.resolution_flags = self.extract_resolution_flags()
        self.escalation_flags = self.extract_escalation_flags()

        # Initialize Gemini (or fallback if needed)
        genai.configure(api_key="your-gemini-api-key")
        self.llm = genai.GenerativeModel("gemini-1.5-flash")

    def load_session(self):
        with open(self.session_json_path, 'r') as f:
            return json.load(f)

    def extract_scores(self):
        return [t['csat_score'] for t in self.session_data.get('history', []) if 'csat_score' in t]

    def extract_resolution_flags(self):
        return [t['issue_resolved'] for t in self.session_data.get('history', []) if 'issue_resolved' in t]

    def extract_escalation_flags(self):
        return [t['escalated'] for t in self.session_data.get('history', []) if 'escalated' in t]

    def compute_summary(self):
        summary = {
            "average_score": round(mean(self.scores), 2) if self.scores else None,
            "total_ratings": len(self.scores),
            "low_score_count": len([s for s in self.scores if s <= 3]),
            "issues_resolved_percent": round(100 * sum(self.resolution_flags) / len(self.resolution_flags), 1) if self.resolution_flags else None,
            "escalation_percent": round(100 * sum(self.escalation_flags) / len(self.escalation_flags), 1) if self.escalation_flags else None
        }
        return summary

    def ask_llm_for_improvement(self):
        summary = self.compute_summary()
        if summary["average_score"] is None:
            return "No CSAT scores available."

        prompt = f"""
        Based on the following CSAT summary:
        - Average Score: {summary['average_score']}
        - Total Ratings: {summary['total_ratings']}
        - Low Ratings (<=3): {summary['low_score_count']}
        - Issues Resolved (%): {summary['issues_resolved_percent']}
        - Escalation Rate (%): {summary['escalation_percent']}

        Suggest ways to improve the chatbot experience.
        Focus on empathy, speed, escalation, and clarity.
        Provide actionable and concise feedback.
        """
        response = self.llm.generate_content(prompt)
        return response.text

# Example Usage
if __name__ == "__main__":
    analyzer = CSATAnalyzer("chat_sessions/session_12345.json")
    print("CSAT Summary:", analyzer.compute_summary())
    print("\nSuggestions to Improve:")
    print(analyzer.ask_llm_for_improvement())
