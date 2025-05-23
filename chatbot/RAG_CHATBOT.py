import os
import json
import uuid
import datetime
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai

# Set up environment and API
os.environ["GOOGLE_API_KEY"] = "your-api-key-here"  # Replace with your actual key or load from .env
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Load FAQs
with open('faq.json', 'r') as f:
    data = json.load(f)

documents = [f"Q: {item['question']}\nA: {item['answer']}" for item in data]
metadatas = [{"question": item["question"]} for item in data]

# Embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embedder.encode(documents, show_progress_bar=True)

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_faq")
collection = chroma_client.get_or_create_collection(name="faq")

if len(collection.get()['ids']) == 0:
    collection.add(
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=[str(i) for i in range(len(documents))]
    )

# Load Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

# Emotion Detection Model
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", return_all_scores=True)

def detect_emotion(text):
    emotions = emotion_classifier(text)[0]
    top_emotion = max(emotions, key=lambda x: x['score'])
    return top_emotion['label'], top_emotion['score']

def add_empathy_to_response(emotion, base_response):
    empathy_prefix = {
        "joy": "That's wonderful to hear! 😊 ",
        "anger": "I'm sorry you're feeling upset. Let's work on this together. ",
        "sadness": "I'm here for you. 💙 ",
        "fear": "Don't worry, I'm here to help. ",
        "surprise": "That's interesting! ",
        "neutral": ""
    }
    return empathy_prefix.get(emotion, "") + base_response

def generate_gemini_answer(query, k=3, similarity_threshold=0.6):
    query_embedding = embedder.encode([query])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    if not results['documents'][0] or len(results['documents'][0]) == 0:
        return None, 0.0  # Return None with low confidence

    context = "\n\n".join(results['documents'][0])
    prompt = f"""You are a helpful and emotionally intelligent assistant. Respond with empathy.

Context:
{context}

Question: {query}
Answer:"""

    response = model.generate_content(prompt)
    # Simulate confidence by inverse of average distance
    avg_score = 1 - sum(results['distances'][0]) / len(results['distances'][0])
    return response.text, avg_score

# CHAT SESSION
session_id = str(uuid.uuid4())
session_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
chat_history_log = []
CONFIDENCE_THRESHOLD = 0.65

print(f"🤖 Gemini EQ Chatbot (Session ID: {session_id}) - Type 'exit' to quit")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Bot: Goodbye!")
        break

    emotion, confidence = detect_emotion(user_input)
    chat_history_log.append(f"User: {user_input} [Emotion: {emotion} ({confidence:.2f})]")

    rag_response, confidence_score = generate_gemini_answer(user_input)

    if rag_response and confidence_score >= CONFIDENCE_THRESHOLD:
        empathetic_response = add_empathy_to_response(emotion, rag_response)
        print("Bot (EQ-RAG):", empathetic_response)
        chat_history_log.append(f"Bot (EQ-RAG): {empathetic_response} [Confidence: {confidence_score:.2f}]")
    else:
        print("Bot: I'm not confident in my answer. Escalating to a human agent... 🧑‍💼")
        chat_history_log.append("Bot: Escalation triggered due to low confidence.")

# Save chat history
with open(f"chat_history_{session_id}.txt", "w", encoding="utf-8") as f:
    f.write(f"Session ID: {session_id}\nStart Time: {session_start_time}\n\n")
    for line in chat_history_log:
        f.write(line + "\n")

# Summarize chat
with open(f"chat_history_{session_id}.txt", "r", encoding="utf-8") as f:
    chat_text = f.read()

summary_prompt = f"Summarize the following emotionally rich conversation briefly:\n\n{chat_text}"
summary_response = model.generate_content(summary_prompt)
print("\nSummary:\n", summary_response.text)

with open(f"summary_{session_id}.txt", "w", encoding="utf-8") as f:
    f.write(summary_response.text)
