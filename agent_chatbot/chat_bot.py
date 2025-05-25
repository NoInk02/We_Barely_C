import os
import json
import uuid
import datetime
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai
import re


class SupportChatBot:
    CHROMA_PATH = "./chroma_company_data"
    COLLECTION_NAME = "company_knowledge"
    TICKETS_PATH = "./tickets_data"
    TICKETS_COLLECTION_NAME = "tickets_collection"
    
    def __init__(self, company_data_file: str, ticket_data_file: str):
        self.company_data_file=company_data_file
        self.ticket_data_file=  ticket_data_file
        
        os.environ["GOOGLE_API_KEY"] = "AIzaSyCSypgJaG3XLvlJvbDg_kg5RbzZm4vf9B8"
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

        self.documents, self.metadatas = self.load_company_data(company_data_file)
        self.collection = self.setup_chroma()

        self.tickets, self.ticket_metadatas = self.load_tickets(self.ticket_data_file)
        self.ticket_lookup = {meta["ticket_id"]: text for meta, text in zip(self.ticket_metadatas, self.tickets)}

        self.ticket_collection = self.setup_ticket_chroma()

        self.session_id = str(uuid.uuid4())
        self.chat_history = []
        self.start_time = datetime.datetime.now()
        self.prompt_count = 0
        client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        try:
            client.delete_collection(name=self.COLLECTION_NAME)
            client.delete_collection(name=self.TICKETS_COLLECTION_NAME)
        except:
            pass
    
    # Now proceed with normal initialization
        self.documents, self.metadatas = self.load_company_data(company_data_file)
        self.collection = self.setup_chroma()
    
        self.tickets, self.ticket_metadatas = self.load_tickets(ticket_data_file)
        self.ticket_lookup = {meta["ticket_id"]: text for meta, text in zip(self.ticket_metadatas, self.tickets)}
    
        self.ticket_collection = self.setup_ticket_chroma()

    def load_company_data(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)

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
                doc = f"{path}: {str(node)}"
                documents.append(doc)
                metadatas.append({"path": path})

        extract_docs(data)
        return documents, metadatas

    def load_tickets(self, file_path):
        print(f"Loading tickets from {file_path}...")  # Debug
        with open(file_path, 'r') as f:
            tickets_data = json.load(f)
        
    # Validation
        if not isinstance(tickets_data, list):
            raise ValueError("Ticket data should be a list of ticket objects")
    
        tickets = []
        ticket_metadatas = []
    
        for ticket in tickets_data:
            if not ticket.get("ticketID"):
                continue  # Skip invalid tickets
            
            text = (
            f"Title: {ticket.get('title', '')}\n"
            f"Category: {ticket.get('category', '')}\n"
            f"Status: {ticket.get('status', '')}\n"
            f"Resolution: {ticket.get('resolution', '')}"
        )
        
            tickets.append(text)
        
            metadata = {
            "ticket_id": ticket["ticketID"],
            "title": ticket.get("title"),
            "status": ticket.get("status"),
            "category": ticket.get("category"),
            "resolution": ticket.get("resolution", "")
        }
            ticket_metadatas.append(metadata)
    
        print(f"Successfully loaded {len(tickets)} tickets")  # Debug
        return tickets, ticket_metadatas

    def setup_chroma(self):
        client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        collection = client.get_or_create_collection(name=self.COLLECTION_NAME)
        existing_ids = collection.get()['ids']

        if len(existing_ids) == 0:
            embeddings = self.embedder.encode(self.documents, show_progress_bar=True)
            collection.add(
                documents=self.documents,
                embeddings=embeddings.tolist(),
                metadatas=self.metadatas,
                ids=[str(i) for i in range(len(self.documents))]
            )
        return collection

    def setup_ticket_chroma(self):
        client = chromadb.PersistentClient(path=self.CHROMA_PATH)
    
    # Force new collection
        try:
            client.delete_collection(name=self.TICKETS_COLLECTION_NAME)
        except:
            pass
        
        collection = client.get_or_create_collection(name=self.TICKETS_COLLECTION_NAME)
    
        if self.tickets:  # Only add if we have tickets
            print(f"Generating embeddings for {len(self.tickets)} tickets...")
            embeddings = self.embedder.encode(self.tickets, show_progress_bar=True)
        
        # Use ticket IDs as ChromaDB IDs for direct lookup
            ids = [meta["ticket_id"] for meta in self.ticket_metadatas]

            collection.add(
            documents=self.tickets,
            embeddings=embeddings.tolist(),
            metadatas=self.ticket_metadatas,
            ids=ids
        )
            print(f"Added tickets to ChromaDB with IDs: {ids[:3]}...")
    
        return collection


    def generate_response(self, query, k=3, ticket_k=3):
        query_embedding = self.embedder.encode([query])[0]

        # 1. Search Knowledge Base
        kb_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        # 2. Search Ticket History
        ticket_results = self.ticket_collection.query(
            query_embeddings=[query_embedding],
            n_results=ticket_k,
            include=["documents", "metadatas", "distances"]
        )

        # 3. Build Combined Context
        context = "Relevant Information for the support agent:\n\n"
        context += "=== Knowledge Base ===\n"
        if kb_results['documents'][0]:
            for doc, meta, dist in zip(kb_results['documents'][0], kb_results['metadatas'][0], kb_results['distances'][0]):
                context += f"[From {meta.get('path', 'unknown')} - Confidence: {1-dist:.2f}]\n{doc}\n\n"
        else:
            context += "No relevant knowledge base entries found.\n\n"

        context += "=== Past Tickets ===\n"
        if ticket_results['documents'][0]:
            for doc, meta, dist in zip(ticket_results['documents'][0], ticket_results['metadatas'][0], ticket_results['distances'][0]):
                context += (
                    f"[Ticket ID: {meta.get('ticket_id', 'unknown')} - Confidence: {1-dist:.2f}]\n"
                    f"Title: {meta.get('title', 'N/A')}\n"
                    f"Status: {meta.get('status', 'N/A')}\n"
                    f"Category: {meta.get('category', 'N/A')}\n"
                    f"Resolution: {meta.get('resolution', 'N/A')}\n\n"
                )
        else:
            context += "No similar past tickets found.\n\n"

        # 4. Compose Prompt
        prompt = f"""You are a support assistant bot designed to help a human support agent resolve tickets efficiently.
    Use the following relevant context, including similar past tickets and knowledge base data, to suggest solutions or next steps.

    Important Guidelines:
    1. Provide precise, actionable advice and troubleshooting steps.
    2. Reference past tickets or documented solutions where applicable.
    3. For common, repetitive issues, suggest possible automation or scripts to speed resolution.
    4. If you cannot find an answer, suggest articles or go find internet solutions.
    5. Do not make up information; only provide what is supported by the context.
    6. DONOT WRITE LONG PARAGRAPHS.

    Context:
    {context}

    Agent's Question: {query}
    Assistant's Answer:"""

        response = self.gemini_model.generate_content(prompt)

        # Average confidence across both sources
        all_dists = []
        if kb_results['distances'][0]:
            all_dists.extend(kb_results['distances'][0])
        if ticket_results['distances'][0]:
            all_dists.extend(ticket_results['distances'][0])
        avg_score = 1 - (sum(all_dists) / len(all_dists)) if all_dists else 0.0

        return response.text, float(avg_score), context


    def suggest_solutions_for_agent(self, ticket_description, k=10, threshold=0.7):
        embedding = self.embedder.encode([ticket_description])[0]
        results = self.ticket_collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["metadatas", "distances"]
        )
        similar_tickets = []
        for meta, dist in zip(results['metadatas'][0], results['distances'][0]):
            similarity = 1 - dist
            if similarity >= threshold:
                similar_tickets.append({
                    "ticket_id": meta["ticket_id"],
                    "title": meta.get("title"),
                    "status": meta.get("status"),
                    "category": meta.get("category"),
                    "confidence": round(similarity, 2)
                })
        return {"similar_tickets": similar_tickets}
    def automate_common_issues(self, ticket_description, threshold=0.85):
        embedding = self.embedder.encode([ticket_description])[0]

        ticket_results = self.ticket_collection.query(
            query_embeddings=[embedding],
            n_results=1,
            include=["documents", "metadatas", "distances"]
        )

        if not ticket_results['documents'][0]:
            return None

        top_sim = 1 - ticket_results['distances'][0][0]
        top_meta = ticket_results['metadatas'][0][0]

        if top_sim >= threshold and top_meta.get("status") == "resolved":
            ticket_id = top_meta.get("ticket_id")
            ticket_file = os.path.join(self.TICKETS_PATH, f"{ticket_id}.json")
            if os.path.exists(ticket_file):
                with open(ticket_file, 'r') as f:
                    ticket_data = json.load(f)
                    resolution = ticket_data.get("resolution")
                    if resolution:
                        return resolution
        return None
    
    def _format_ticket_response(self, ticket_id):
        """Format consistent ticket responses"""
    # Try to get full metadata
        ticket_meta = next(
            (m for m in self.ticket_metadatas if m["ticket_id"].lower() == ticket_id.lower()),
            None
        )
    
        if ticket_meta:
            response = (
                f"Ticket {ticket_id}:\n"
                f"• Title: {ticket_meta.get('title', 'N/A')}\n"
                f"• Status: {ticket_meta.get('status', 'N/A')}\n"
                f"• Category: {ticket_meta.get('category', 'N/A')}\n"
                f"• Resolution: {ticket_meta.get('resolution', 'Pending')}"
            )
        else:
            response = f"Found ticket {ticket_id} but missing details"
    
        return {
            "session_id": self.session_id,
            "response": response,
            "confidence": 1.0,
            "context": None
        }

    def link_related_tickets(self, new_ticket_description, similarity_threshold=0.75):
        embedding = self.embedder.encode([new_ticket_description])[0]

        ticket_results = self.ticket_collection.query(
            query_embeddings=[embedding],
            n_results=10,
            include=["metadatas", "distances"]
        )

        related_ticket_ids = []
        for meta, dist in zip(ticket_results['metadatas'][0], ticket_results['distances'][0]):
            similarity = 1 - dist
            if similarity >= similarity_threshold:
                related_ticket_ids.append(meta.get("ticket_id"))
        return related_ticket_ids      

    def process_query(self, input_dict):
        query = input_dict.get('query')
        if not query:
            return {"error": "No query provided."}

    # Improved ticket ID matching (case-insensitive, handles more formats)
        ticket_id_match = re.search(r"(?i)\b([tT][0-9a-z\-]{20,36})\b", query)
        if ticket_id_match:
            ticket_id = ticket_id_match.group(1).lower()
            print(f"Looking up ticket: {ticket_id}")  # Debug
            if ticket_id in self.ticket_lookup:
                return self._format_ticket_response(ticket_id)
    
        # Case-insensitive search through ticket_lookup keys
            matched_ticket_id = None
            for tid in self.ticket_lookup.keys():
                if tid.lower() == ticket_id:
                    matched_ticket_id = tid
                    break
            results = self.ticket_collection.get(ids=[ticket_id])
            if results['ids']:
                return self._format_ticket_response(ticket_id)
            if matched_ticket_id:
                ticket_text = self.ticket_lookup[matched_ticket_id]
            
                # Try to get structured metadata for richer response
                ticket_meta = next(
                    (meta for meta in self.ticket_metadatas 
                    if meta.get("ticket_id", "").lower() == ticket_id),
                    None
                )
            
                response_text = f"Ticket {matched_ticket_id} Details:\n"
                if ticket_meta:
                    response_text += f"• Title: {ticket_meta.get('title', 'N/A')}\n"
                    response_text += f"• Status: {ticket_meta.get('status', 'N/A')}\n"
                    response_text += f"• Priority: {ticket_meta.get('priority', 'N/A')}\n"
                    response_text += f"• Category: {ticket_meta.get('category', 'N/A')}\n"
                    if ticket_meta.get('resolution'):
                        response_text += f"• Resolution: {ticket_meta['resolution']}\n"
                    response_text += f"• Summary: {ticket_meta.get('summary', 'N/A')}"
                else:
                    response_text += ticket_text

                return {
                    "session_id": self.session_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "response": response_text,
                "confidence": 1.0,
                "context": None
            }
            else:
                return {
                    "session_id": self.session_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "response": f"No information found for ticket ID {ticket_id} in our records.",
                "confidence": 0.0,
                "context": None,
                "suggestion": "Please verify the ticket ID or contact support if you believe this is an error."
            }

    # Fallback to general query processing
        self.prompt_count += 1
        response, confidence, context = self.generate_response(query)
    
        timestamp = datetime.datetime.now().isoformat()
        self.chat_history.append({
        "input": query,
        "response": response,
        "confidence": confidence,
        "timestamp": timestamp
    })

        return {
        "session_id": self.session_id,
        "timestamp": timestamp,
        "response": response,
        "confidence": confidence,
        "context": context
    }

    def end_session(self):
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        average_confidence = sum(turn['confidence'] for turn in self.chat_history) / len(self.chat_history) if self.chat_history else 0
        session_data = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "prompt_count": self.prompt_count,
            "average_confidence": average_confidence,
            "history": self.chat_history
        }

        os.makedirs("chat_sessions", exist_ok=True)
        filename = f"chat_sessions/session_{self.session_id}.json"
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2)

        return session_data
