import os
import json
import uuid
import datetime
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai
from config.config import settings


class SupportChatBot:

    CHROMA_PATH = "./chroma_company_data"
    COLLECTION_NAME = "company_knowledge"

    def __init__(self, company_data):
        # Configure API key for Google Generative AI
        genai.configure(api_key=settings.GEMINI_API_KEY)

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

        self.documents, self.metadatas = self.load_company_data(company_data)
        self.collection = self.setup_chroma(        )
        self.embedder.encode(self.documents, show_progress_bar=True, normalize_embeddings=True)
        self.chatID = None
        self.session_id = str(uuid.uuid4())
        self.chat_history = []
        self.start_time = datetime.datetime.now()
        self.chat = self.gemini_model.start_chat(history=[])
        self.prompt_count = 0

    def load_company_data(self, data):

        documents = []
        metadatas = []

        def extract_docs(node, path=""):
            if isinstance(node, dict):
                for key, value in node.items():
                    new_path = f"{path}/{key}" if path else key
                    extract_docs(value, new_path)
            elif isinstance(node, list):
                for idx, item in enumerate(node):
                    new_path = f"{path}[{idx}]"
                    extract_docs(item, new_path)
            else:
                # Leaf node (string, number, bool, etc.)
                doc = f"{path}: {str(node)}"
                documents.append(doc)
                metadatas.append({"path": path})

        extract_docs(data)

        return documents, metadatas

    def setup_chroma(self):
        client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        collection = client.get_or_create_collection(name=self.COLLECTION_NAME)
        embeddings = self.embedder.encode(self.documents, show_progress_bar=True, normalize_embeddings=True)

        if len(collection.get()['ids']) == 0:
            collection.add(
                documents=self.documents,
                embeddings=embeddings.tolist(),
                metadatas=self.metadatas,
                ids=[str(i) for i in range(len(self.documents))]
            )
        return collection

    
    def detect_emotion(self, text):
        emotions = self.emotion_classifier(text)[0]
        top_emotion = max(emotions, key=lambda x: x['score'])
        return top_emotion['label'], float(top_emotion['score'])

    def generate_response(self, query, k=3):
        query_embedding = self.embedder.encode([query], normalize_embeddings=True)[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        if not results['documents'][0]:
            return "I'm sorry, I couldn't find relevant information to help with that.", 0.0, None

        context = "Relevant Information:\n\n"
        for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            confidence_for_doc = max(0.0, 1 - dist)
            context += f"[From {meta.get('path', 'Unknown')} - Confidence: {confidence_for_doc:.2f}]\n"
            context += f"{doc}\n\n"

        emotion, _ = self.detect_emotion(query)

        recent_turns = self.chat_history[-3:]
        prior_conversation = "\n".join([f"User: {t['input']}\nBot: {t['response']}" for t in recent_turns])

        prompt = f"""You are a customer support assistant for SwiftShip Logistics.

    Prior conversation:
    {prior_conversation}

    The user now says:
    {query}

    Use the following context to answer professionally:

    {context}

    Important Guidelines:
    1. Be consistent with prior answers if repeated
    2. Use short, professional, emotionally aware language
    3. If unsure or angry, suggest escalation
    Answer:"""

        response = self.chat.send_message(prompt)
        best_distance = min(results['distances'][0])
        confidence_score = max(0.0, 1 - best_distance)

        return response.text, confidence_score, context

    def process_query(self, input_dict):
        """
        Accepts: input_dict with key 'query'
        Returns: dict with keys 'response', 'emotion', 'confidence', 'session_id', 'timestamp', optionally 'context'
        """

        query = input_dict.get('query')
        if not query:
            return {"error": "No query provided."}

        self.prompt_count += 1

        emotion, emotion_score = self.detect_emotion(query)
        response, confidence, context = self.generate_response(query)

        timestamp = datetime.datetime.now().isoformat()

        # Save chat turn
        self.chat_history.append({
            "input": query,
            "response": response,
            "emotion": {"label": emotion, "score": emotion_score},
            "confidence": confidence,
            "timestamp": timestamp
        })

        return {
            "session_id": self.session_id,
            "timestamp": timestamp,
            "response": response,
            "emotion": {"label": emotion, "score": emotion_score},
            "confidence": confidence
            # "context": context  # Optional, can remove if you want less verbose output
        }

    def end_session(self):
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        average_confidence = sum(turn['confidence'] for turn in self.chat_history) / len(self.chat_history) if self.chat_history else 0
        emotion_distribution = {}
        for turn in self.chat_history:
            label = turn['emotion']['label']
            emotion_distribution[label] = emotion_distribution.get(label, 0) + 1

        session_data = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "prompt_count": self.prompt_count,
            "average_confidence": average_confidence,
            "emotion_distribution": emotion_distribution,
            "history": self.chat_history
        }

        return session_data
