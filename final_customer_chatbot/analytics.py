import matplotlib.pyplot as plt
import numpy as np

# Dummy data for analytics (based on provided parameters)
data = {
    "average_score": [3, 4, 2, 5, 3],
    "average_handling_time": [82.0, 60.5, 100.3, 70.0, 89.2],
    "average_confidence": [0.33, 0.6, 0.45, 0.75, 0.55],
    "low_score_count": [1, 0, 2, 0, 1],
    "emotion_distribution": [
        {"neutral": 2, "sadness": 2, "joy": 1},
        {"neutral": 3, "sadness": 0, "joy": 2},
        {"neutral": 1, "sadness": 4, "joy": 0},
        {"neutral": 4, "sadness": 0, "joy": 3},
        {"neutral": 2, "sadness": 1, "joy": 2}
    ]
}

# Plot average CSAT score over sessions
plt.figure(figsize=(8, 5))
plt.plot(data['average_score'], marker='o', label='Average CSAT')
plt.title("Average CSAT Score Over Sessions")
plt.xlabel("Session Index")
plt.ylabel("CSAT Score")
plt.ylim(0, 5)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Plot average handling time
plt.figure(figsize=(8, 5))
plt.bar(range(len(data['average_handling_time'])), data['average_handling_time'], color='orange')
plt.title("Average Handling Time Per Session")
plt.xlabel("Session Index")
plt.ylabel("Time (seconds)")
plt.tight_layout()
plt.show()

# Plot average model confidence
plt.figure(figsize=(8, 5))
plt.plot(data['average_confidence'], marker='x', color='green')
plt.title("Average Response Confidence")
plt.xlabel("Session Index")
plt.ylabel("Confidence Score")
plt.ylim(0, 1)
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot low score counts
plt.figure(figsize=(8, 5))
plt.bar(range(len(data['low_score_count'])), data['low_score_count'], color='red')
plt.title("Low CSAT Score Counts")
plt.xlabel("Session Index")
plt.ylabel("# of Low Ratings")
plt.tight_layout()
plt.show()

# Plot emotion distribution (stacked bar chart)
sessions = range(len(data['emotion_distribution']))
neutral = [e['neutral'] for e in data['emotion_distribution']]
sadness = [e['sadness'] for e in data['emotion_distribution']]
joy = [e['joy'] for e in data['emotion_distribution']]

plt.figure(figsize=(10, 6))
plt.bar(sessions, neutral, label='Neutral')
plt.bar(sessions, sadness, bottom=neutral, label='Sadness')
plt.bar(sessions, joy, bottom=[neutral[i] + sadness[i] for i in sessions], label='Joy')
plt.title("Emotion Distribution Per Session")
plt.xlabel("Session Index")
plt.ylabel("Count")
plt.legend()
plt.tight_layout()
plt.show()
