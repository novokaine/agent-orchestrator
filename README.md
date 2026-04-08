# 🏭 Agent Factory

> A fully self-hosted agent system that can generate, execute, and manage code using a local LLM, sandboxed runtime, and real-time UI.

---

## 🚨 What This Project Is

Agent Factory is a **containerized AI system** designed to:

- Run agents using a **local LLM (Ollama)**
- Persist state and data (MongoDB)
- Coordinate execution (FastAPI backend)
- Execute generated code in an isolated **Docker sandbox**
- Stream results to a **real-time React UI**

> This is not a chatbot. It is an **execution system**.

---

## 🧩 System Architecture


┌───────────────┐
│ Frontend UI │ (React + WebSocket)
└───────┬───────┘
│
▼
┌───────────────┐
│ Agent Backend │ (FastAPI)
│ Orchestrator │
└───────┬───────┘
│
┌──────┼───────────────┐
▼ ▼ ▼
LLM Database Cache
(Ollama) (MongoDB) (Redis)
│
▼
┌───────────────┐
│ Docker Sandbox│
│ Code Execution│
└───────────────┘


---

## ⚙️ Core Components

### 🧠 LLM Layer
- Powered by **Ollama**
- Runs fully local models (e.g. `llama3`)
- No external dependency required

---

### 🧩 Backend (Agent Orchestrator)
- Built with **FastAPI**
- Handles:
  - agent logic
  - request processing
  - execution flow

Key modules:
- `agents/orchestrator.py`
- `models/schema.py`
- `database/mongo.py`

---

### 🗄️ Persistence
- **MongoDB**
  - Stores agent data, history, and state

---

### ⚡ Realtime Layer
- **Redis**
  - WebSocket state
  - caching

---

### 🧪 Execution Sandbox
- Docker-in-Docker (`dind`)
- Executes generated code safely
- Projects written to:

/projects


---

### 🖥️ Frontend
- React + Vite
- WebSocket-based communication
- Live updates from agent execution

---

## 📦 Infrastructure (Docker)

The entire system runs via `docker-compose`:

### Services

- `ollama` → local LLM server  
- `mongodb` → persistence  
- `redis` → state / caching  
- `agent-orchestrator` → FastAPI backend  
- `sandbox` → isolated execution environment  
- `frontend-ui` → React UI  
- `nginx` → optional production proxy  

---

## ▶️ Getting Started

### 1. Setup environment

Create `.env`:

```env
MONGO_ROOT_USER=admin
MONGO_ROOT_PASS=password
REDIS_PASSWORD=redispass
SECRET_KEY=supersecret
2. Start system
docker-compose up --build
3. Access
UI → http://localhost:3000
API → http://localhost:8000
🔁 Execution Flow
User interacts via UI
Request sent to FastAPI backend
Orchestrator processes input
LLM generates output (via Ollama)
Code (if any) executed in sandbox
Results stored (MongoDB)
Updates streamed via WebSocket
📁 Project Structure
agent-factory/
├── agent-orchestrator/   # FastAPI backend
├── frontend-ui/          # React UI
├── mongodb/              # DB init scripts
├── projects/             # generated code output
├── docker-compose.yml
└── .env
🎯 What Makes This Different
✅ Fully self-hosted (no SaaS dependency)
✅ Real code execution (not just text output)
✅ Isolated sandbox (safe execution)
✅ End-to-end system (LLM → execution → UI)
✅ Production-ready structure (Dockerized)
⚠️ Current Limitations
No advanced planning system yet
Sandbox security can be hardened further
Limited agent specialization
UI is minimal
🛣️ Future Improvements
Multi-agent coordination
Task planning layer
Better execution tracing
Role-based agents
Improved UI/UX