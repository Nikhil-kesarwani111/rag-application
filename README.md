# 📚 RAG PDF Chat Application

A full-stack **Retrieval-Augmented Generation (RAG)** application that allows users to upload private PDF documents and chat with them using Large Language Models (LLMs).  
The system retrieves relevant information from documents using vector search and generates accurate, source-grounded answers in real time.

---
<img width="1902" height="968" alt="image" src="https://github.com/user-attachments/assets/4abfc000-1db3-4f23-aa13-fb48e8751a2c" />
##🎥 Project Demo

[![Watch the demo](https://img.youtube.com/vi/UmgLljbn0nQ/0.jpg)](https://youtu.be/UmgLljbn0nQ)



## 🚀 Features

- 📄 Upload multiple PDF documents
- 🔍 Semantic search using vector embeddings
- 🤖 LLM-powered question answering (RAG)
- ⚡ Real-time streaming responses (Server-Sent Events)
- 📌 Source citation from original PDFs
- 🐳 Docker-based vector database (pgvector)
- 🌐 Modern React frontend (Vite + TypeScript)

---

## 🏗️ Architecture Overview

Frontend (React + Vite)
│
│ HTTP / SSE
▼
Backend (FastAPI + LangServe)
│
│ Vector Search
▼
PostgreSQL + pgvector


---

## 🧠 Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Server-Sent Events (SSE)

### Backend
- FastAPI
- LangChain
- LangServe
- Python 3.11
- Poetry

### Vector Database
- PostgreSQL
- pgvector
- Docker (local development)

---

## 📂 Project Structure

rag-application/
├── frontend/ # React + Vite frontend
├── app/ # FastAPI backend (LangServe)
├── packages/ # Shared / helper packages
├── tests/ # Backend tests
├── Dockerfile # Backend container
├── pyproject.toml # Poetry dependencies
├── poetry.lock
├── README.md
└── .gitignore


---

## ⚙️ Local Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Nikhil-kesarwani111/rag-application.git
cd rag-application

Backend Setup (FastAPI + LangServe)
poetry install
poetry shell
uvicorn app.server:app --reload

### 2️⃣ Backend Setup (FastAPI + LangServe)
poetry install
poetry shell
uvicorn app.server:app --reload


Backend runs at:

http://127.0.0.1:8000


LangServe Playground:

http://127.0.0.1:8000/rag/playground

3️⃣ Frontend Setup (React)
cd frontend
npm install
npm run dev


Frontend runs at:

http://localhost:5173

4️⃣ Vector Database (pgvector via Docker)
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ragdb \
  pgvector/pgvector:pg16

🔐 Environment Variables

Create a .env file (do not commit it):

DATABASE_URL=postgresql://user:password@host:5432/db
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

🔄 API Endpoints
Method	Endpoint	Description
POST	/upload	Upload PDF files
POST	/load-and-process-pdfs	Process PDFs into vectors
POST	/rag/stream	Stream chat responses
GET	/rag/static/{file}	Download source PDF
