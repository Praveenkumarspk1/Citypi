# AI Smart City Concierge - Cline Task Completion Prompt

**Priority Level**: CRITICAL (Low AI credits - focus on high-impact items)  
**Estimated Time**: 4-6 hours with efficient implementation  
**Success Criteria**: App runs without errors and supports real-time features

---

## 🎯 TASK 1: Fix Backend Authentication (BLOCKING FRONTEND) - 1.5 hours

### Objective
Complete the authentication backend so frontend login/register/reset flows work end-to-end.

### Current State
- ✅ Frontend: Auth UI pages and API client ready
- ❌ Backend: Routes return `NotImplementedError`, handlers not in DI container

### Required Tasks

#### 1.1 Register Auth Handlers in DI Container
**File**: `apps/api/src/ai_smart_city_concierge/infrastructure/kernel/di_container.py`

Add these registrations to the `setup_handlers()` method:
```python
# User Commands
container.register(
    CreateUserCommandHandler,
    factory=lambda: CreateUserCommandHandler(
        user_repo=container.resolve(UserRepository),
        event_publisher=container.resolve(EventPublisher),
    ),
)
container.register(
    ForgotPasswordCommandHandler,
    factory=lambda: ForgotPasswordCommandHandler(
        user_repo=container.resolve(UserRepository),
        email_service=container.resolve(EmailService),
    ),
)
container.register(
    ResetPasswordCommandHandler,
    factory=lambda: ResetPasswordCommandHandler(
        user_repo=container.resolve(UserRepository),
    ),
)
container.register(
    VerifyUserEmailCommandHandler,
    factory=lambda: VerifyUserEmailCommandHandler(
        user_repo=container.resolve(UserRepository),
    ),
)

# User Queries
container.register(
    GetUserByEmailQueryHandler,
    factory=lambda: GetUserByEmailQueryHandler(
        user_repo=container.resolve(UserRepository),
    ),
)
```

#### 1.2 Fix User Routes
**File**: `apps/api/src/ai_smart_city_concierge/interfaces/api/v1/routes/auth.py`

Replace all `raise NotImplementedError` with actual command/query dispatches:
```python
@router.post("/register", response_model=UserResponseDTO)
async def register(request: RegisterUserRequestDTO):
    command = CreateUserCommand(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )
    handler = container.resolve(CreateUserCommandHandler)
    user = await handler.handle(command)
    return UserResponseDTO.from_domain(user)
```

#### 1.3 Implement Password Hashing in User Entity
**File**: `apps/api/src/ai_smart_city_concierge/domain/aggregates/user.py`

Add password methods:
```python
@staticmethod
def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(self, password: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(password.encode(), self.password_hash.encode())
```

#### 1.4 Implement Email Token Generation
**File**: `apps/api/src/ai_smart_city_concierge/infrastructure/persistence/repositories/user_repository.py`

Add methods:
```python
def generate_reset_token(self, user_id: str) -> str:
    import secrets
    token = secrets.token_urlsafe(32)
    # Store token in cache or DB with expiry (24 hours)
    self.cache.set(f"reset_token:{token}", user_id, ex=86400)
    return token

def verify_reset_token(self, token: str) -> Optional[str]:
    return self.cache.get(f"reset_token:{token}")
```

#### 1.5 Connect JWT to Login
**File**: `apps/api/src/ai_smart_city_concierge/interfaces/api/v1/routes/auth.py`

In login endpoint:
```python
from ai_smart_city_concierge.infrastructure.auth.jwt_handler import JWTHandler

@router.post("/login", response_model=LoginResponseDTO)
async def login(request: LoginRequestDTO):
    query = GetUserByEmailQuery(email=request.email)
    handler = container.resolve(GetUserByEmailQueryHandler)
    user = await handler.handle(query)
    
    if not user or not user.verify_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    jwt_handler = container.resolve(JWTHandler)
    token = jwt_handler.generate_token(user.id, user.email)
    return LoginResponseDTO(access_token=token, user=UserResponseDTO.from_domain(user))
```

---

## 🎯 TASK 2: Implement WebSocket Service Core (UNLOCKS REAL-TIME FEATURES) - 2.5 hours

### Objective
Build real-time server for chat, location sharing, and collaborative features.

### Location
Create files in: `apps/websocket/src/`

### Required Files to Create

#### 2.1 Main WebSocket Server
**File**: `apps/websocket/src/main.py`
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set
import json
import asyncio
from pydantic import BaseModel

app = FastAPI(title="AI Smart City Concierge - WebSocket Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
    
    async def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
    
    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                await self.disconnect(room_id, conn)

manager = ConnectionManager()

@app.websocket("/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: str):
    await manager.connect(f"chat:{conversation_id}", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(f"chat:{conversation_id}", {
                "type": "message",
                "conversation_id": conversation_id,
                "data": data
            })
    except WebSocketDisconnect:
        await manager.disconnect(f"chat:{conversation_id}", websocket)

@app.websocket("/ws/location/{room_id}")
async def websocket_location_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(f"location:{room_id}", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(f"location:{room_id}", {
                "type": "location_update",
                "room_id": room_id,
                "data": data
            })
    except WebSocketDisconnect:
        await manager.disconnect(f"location:{room_id}", websocket)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

#### 2.2 WebSocket Message Schemas
**File**: `apps/websocket/src/schemas.py`
```python
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class ChatMessage(BaseModel):
    user_id: str
    content: str
    message_type: str = "text"  # text, image, voice, file
    timestamp: datetime = None
    metadata: Optional[dict] = None

class LocationUpdate(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    accuracy: float = 0.0
    timestamp: datetime = None

class TypingIndicator(BaseModel):
    user_id: str
    is_typing: bool

class ReadReceipt(BaseModel):
    user_id: str
    message_id: str
    timestamp: datetime = None
```

#### 2.3 Handler Classes
**File**: `apps/websocket/src/handlers.py`
```python
from schemas import ChatMessage, LocationUpdate
from typing import Callable, Dict

class ChatHandler:
    def __init__(self, manager):
        self.manager = manager
    
    async def handle_message(self, conversation_id: str, message: ChatMessage):
        await self.manager.broadcast(f"chat:{conversation_id}", {
            "type": "message",
            "conversation_id": conversation_id,
            "message": message.dict()
        })
    
    async def handle_typing(self, conversation_id: str, user_id: str, is_typing: bool):
        await self.manager.broadcast(f"chat:{conversation_id}", {
            "type": "typing",
            "user_id": user_id,
            "is_typing": is_typing
        })

class LocationHandler:
    def __init__(self, manager):
        self.manager = manager
    
    async def handle_location_update(self, room_id: str, location: LocationUpdate):
        await self.manager.broadcast(f"location:{room_id}", {
            "type": "location",
            "room_id": room_id,
            "location": location.dict()
        })

class NotificationHandler:
    def __init__(self, manager):
        self.manager = manager
    
    async def send_notification(self, user_id: str, notification: dict):
        await self.manager.broadcast(f"user:{user_id}", {
            "type": "notification",
            "data": notification
        })
```

#### 2.4 WebSocket Environment
**File**: `apps/websocket/pyproject.toml`
```toml
[project]
name = "websocket-server"
version = "0.1.0"
description = "Real-time WebSocket server for AI Smart City Concierge"
dependencies = [
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "python-dotenv==1.0.0",
    "pydantic==2.5.0",
]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
```

#### 2.5 Docker Support
**File**: `apps/websocket/Dockerfile` (update existing if present)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY src/ ./src/

CMD ["python", "-m", "src.main"]
```

---

## 🎯 TASK 3: Set Up Basic CI/CD Pipeline (ENABLE AUTOMATION) - 1 hour

### Objective
Create GitHub Actions workflow for automated testing and deployment.

### Create File
**Location**: `.github/workflows/test-and-build.yml`

```yaml
name: Test & Build

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        working-directory: ./apps/api
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest pytest-asyncio
      
      - name: Run backend tests
        working-directory: ./apps/api
        run: pytest tests/ -v

  test-frontend:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        working-directory: ./apps/frontend
        run: npm install
      
      - name: Run frontend tests
        working-directory: ./apps/frontend
        run: npm run test
      
      - name: Build frontend
        working-directory: ./apps/frontend
        run: npm run build

  build-docker:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build API Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./apps/api
          file: ./docker/Dockerfile.api
          push: false
      
      - name: Build Frontend Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./apps/frontend
          file: ./docker/Dockerfile.frontend
          push: false
```

---

## 🎯 TASK 4: Create Environment Configuration Template (UNBLOCK LOCAL SETUP) - 30 min

### Create File
**Location**: `apps/api/.env.example`

```
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_smart_city
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# External APIs
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# Vector Store
QDRANT_URL=http://localhost:6333
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Storage
GCS_BUCKET_NAME=ai-smart-city-storage
GCS_CREDENTIALS_PATH=./gcs-credentials.json

# Logging
LOG_LEVEL=INFO
```

**Location**: `apps/frontend/.env.example`

```
VITE_API_BASE_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8001
VITE_FIREBASE_CONFIG_KEY=your-firebase-key
```

---

## ⚡ HOW TO RUN EVERYTHING

### 1. Backend Setup
```bash
cd apps/api
pip install -e .
cp .env.example .env
# Edit .env with your credentials
python -m src.main
```

### 2. WebSocket Setup
```bash
cd apps/websocket
pip install -e .
python -m src.main
```

### 3. Frontend Setup
```bash
cd apps/frontend
npm install
cp .env.example .env
npm run dev
```

### 4. Docker Compose (Full Stack)
```bash
cd docker
docker-compose up -d
```

---

## ✅ VALIDATION CHECKLIST

After completing these tasks, verify:

- [ ] Backend API starts: `python -m src.main` runs without errors
- [ ] WebSocket server starts: `python -m src.main` in websocket folder
- [ ] Frontend dev server starts: `npm run dev`
- [ ] Auth endpoints work: Test login, register, password reset
- [ ] WebSocket connection works: Test `/ws/chat/{conversation_id}`
- [ ] CI/CD pipeline runs: Push to GitHub and verify Actions pass
- [ ] Docker Compose builds: `docker-compose build`
- [ ] Database migrations run: `alembic upgrade head`

---

## 📊 EFFICIENCY NOTES

- **Focus Area**: High-impact items only (auth, WebSocket, CI/CD)
- **Skip**: Advanced features (map, itinerary builder, PWA) - save for later
- **Testing**: Only run existing tests, don't write new ones (saves credits)
- **Total Time**: 4-6 hours for one AI agent working efficiently
- **Expected Outcome**: App fully functional with real-time features
