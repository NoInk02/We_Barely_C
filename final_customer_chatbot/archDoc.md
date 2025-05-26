# 💬 SwiftShip Support Chatbot

A customer support chatbot for SwiftShip Logistics that uses **Gemini**, **semantic search**, and **emotion-aware response generation** to deliver accurate, context-rich, and empathetic answers.

---

## ✨ Features

- 🔍 **Retrieval-Augmented Generation (RAG)** using ChromaDB + SentenceTransformers
- 🧠 **Emotion detection** from user queries (angry, sad, happy, etc.)
- 🤖 **Gemini 1.5 Flash**-based response generation with dynamic prompt conditioning
- 💾 **Session logging** with emotion & confidence tracking
- 📝 **Feedback collection** and Gemini-based chat summaries

---

## 🏗️ Architecture Overview

```text
 User Input
    │
    ▼
[Emotion Detection] ◄────────────┐
    │                            │
    ▼                            │
[Query Embedding]                │
    │                            │
    ▼                            │
[Semantic Search in ChromaDB]    │
    │                            │
    ▼                            │
[Build Gemini Prompt with Context & Emotion]
    │
    ▼
[Gemini 1.5 Flash Response]
    │
    ▼
[Log to Session File]
    │
    ▼
[Feedback Prompt (manual or Gemini-generated)]
