import matplotlib.pyplot as plt
import json
from typing import List


def load_analytics_data(json_path: str):
    with open(json_path, "r") as f:
        return json.load(f)

def prepare_plot_data(data: List[dict]):
    average_scores = []
    handling_times = []
    confidences = []
    low_scores = []
    emotion_neutral = []
    emotion_sadness = []
    emotion_joy = []

    for record in data:
        summary = record["summary"]
        average_scores.append(summary["average_score"])
        handling_times.append(summary["average_handling_time"])
        confidences.append(summary["average_confidence"])
        low_scores.append(summary["low_score_count"])
        emotion_neutral.append(summary["emotion_distribution"].get("neutral", 0))
        emotion_sadness.append(summary["emotion_distribution"].get("sadness", 0))
        emotion_joy.append(summary["emotion_distribution"].get("joy", 0))

    return average_scores, handling_times, confidences, low_scores, emotion_neutral, emotion_sadness, emotion_joy

def plot_analytics(json_path: str):
    data = load_analytics_data(json_path)
    average_scores, handling_times, confidences, low_scores, emotion_neutral, emotion_sadness, emotion_joy = prepare_plot_data(data)
    sessions = list(range(len(average_scores)))

    # Plot average score
    plt.figure(figsize=(8, 5))
    plt.plot(sessions, average_scores, marker='o', label='Average CSAT')
    plt.title("Average CSAT Score Over Sessions")
    plt.xlabel("Session Index")
    plt.ylabel("CSAT Score")
    plt.ylim(0, 5)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plot handling times
    plt.figure(figsize=(8, 5))
    plt.bar(sessions, handling_times, color='orange')
    plt.title("Average Handling Time Per Session")
    plt.xlabel("Session Index")
    plt.ylabel("Time (seconds)")
    plt.tight_layout()
    plt.show()

    # Plot confidences
    plt.figure(figsize=(8, 5))
    plt.plot(sessions, confidences, marker='x', color='green')
    plt.title("Average Response Confidence")
    plt.xlabel("Session Index")
    plt.ylabel("Confidence Score")
    plt.ylim(-1, 1)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Plot low score counts
    plt.figure(figsize=(8, 5))
    plt.bar(sessions, low_scores, color='red')
    plt.title("Low CSAT Score Counts")
    plt.xlabel("Session Index")
    plt.ylabel("# of Low Ratings")
    plt.tight_layout()
    plt.show()

    # Emotion distribution (stacked bar)
    plt.figure(figsize=(10, 6))
    plt.bar(sessions, emotion_neutral, label='Neutral')
    plt.bar(sessions, emotion_sadness, bottom=emotion_neutral, label='Sadness')
    plt.bar(sessions, emotion_joy, bottom=[emotion_neutral[i] + emotion_sadness[i] for i in sessions], label='Joy')
    plt.title("Emotion Distribution Per Session")
    plt.xlabel("Session Index")
    plt.ylabel("Count")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Return for frontend use
    return {
        "average_scores": average_scores,
        "handling_times": handling_times,
        "confidences": confidences,
        "low_scores": low_scores,
        "emotion_neutral": emotion_neutral,
        "emotion_sadness": emotion_sadness,
        "emotion_joy": emotion_joy
    }

# Example usage (comment out in actual frontend deployment)
if __name__ == "__main__":
    results = plot_analytics("dummy.json")
    print("Processed Analytics:", results)
