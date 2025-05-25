import os
import json
import uuid
import datetime
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai

class SupportChatBot:
    CHROMA_PATH = "./chroma_company_data"
    COLLECTION_NAME = "company_knowledge"

    def __init__(self, company_data_file='company_data.json'):
        # Configure API key for Google Generative AI
        os.environ["GOOGLE_API_KEY"] = "AIzaSyCSypgJaG3XLvlJvbDg_kg5RbzZm4vf9B8"
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

        self.documents, self.metadatas = self.load_company_data(company_data_file)
        self.collection = self.setup_chroma()

        self.session_id = str(uuid.uuid4())
        self.chat_history = []
        self.start_time = datetime.datetime.now()
        self.prompt_count = 0

    def load_company_data(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)

        documents = []
        metadatas = []

        company_info = data["company_info"]
        doc = "Company Information:\n"
        doc += f"Name: {company_info['name']}\n"
        doc += f"Address: {company_info['address']}\n"
        doc += f"Contact: {company_info['contact_email']} | {company_info['support_number']}\n"
        doc += f"Hours: {company_info['working_hours']}"
        documents.append(doc)
        metadatas.append({"category": "company_info", "type": "general"})

        for policy, details in data["policies"].items():
            doc = f"Policy: {policy.replace('_', ' ').title()}\n{details}"
            documents.append(doc)
            metadatas.append({"category": "policies", "type": policy})

        for service in data["services"]:
            doc = f"Service: {service['name']}\n"
            doc += f"Description: {service['description']}\n"
            doc += f"Price: {service['price_per_kg']}"
            documents.append(doc)
            metadatas.append({"category": "services", "type": service['name'].lower().replace(' ', '_')})

        for faq in data["faqs"]:
            doc = f"FAQ:\nQ: {faq['question']}\nA: {faq['answer']}"
            documents.append(doc)
            metadatas.append({"category": "faqs", "type": "general"})

        for issue in data["troubleshooting"]:
            doc = f"Troubleshooting: {issue['issue']}\nSteps:\n"
            doc += "\n".join([f"- {step}" for step in issue["steps"]])
            documents.append(doc)
            metadatas.append({"category": "troubleshooting", "type": issue['issue'].lower().replace(' ', '_')})

        esc = data["escalation"]
        doc = "Escalation Info:\n"
        doc += f"Triggers: {esc['human_contact_trigger']}\n"
        doc += f"Email: {esc['email_for_escalation']}\n"
        doc += f"Portal: {esc['support_ticket_url']}"
        documents.append(doc)
        metadatas.append({"category": "escalation", "type": "contact"})

        return documents, metadatas

    def setup_chroma(self):
        client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        collection = client.get_or_create_collection(name=self.COLLECTION_NAME)
        embeddings = self.embedder.encode(self.documents, show_progress_bar=True)

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
        query_embedding = self.embedder.encode([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        if not results['documents'][0]:
            return None, 0.0, None

        context = "Relevant Information:\n\n"
        for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            context += f"[From {meta['category'].title()} - Confidence: {1-dist:.2f}]\n"
            context += f"{doc}\n\n"

        emotion, _ = self.detect_emotion(query)

        prompt = f"""You are a customer support assistant for SwiftShip Logistics. 
The user appears to be feeling {emotion}. Use the following context to answer professionally:

{context}

Important Guidelines:
1. For policy questions, be precise and quote exact terms when possible
2. For service inquiries, include pricing if available
3. For troubleshooting, list steps clearly
4. If emotion is anger or you are unable to answer, ask the user if he wants to raise a ticket.
5. Never make up information
6. Act Professionally and concise your answers, not big paragraphs.

Question: {query}
Answer:"""

        response = self.gemini_model.generate_content(prompt)
        avg_score = 1 - sum(results['distances'][0]) / len(results['distances'][0])

        return response.text, float(avg_score), context

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
            "confidence": confidence,
            "context": context  # Optional, can remove if you want less verbose output
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

        # Save session file
        os.makedirs("chat_sessions", exist_ok=True)
        filename = f"chat_sessions/session_{self.session_id}.json"
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2)

        return session_data
