import json
import os
from typing import List, Optional, Union, Literal, Annotated
from enum import Enum
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.staticfiles import StaticFiles  # <--- Импорт для статики
from fastapi.responses import FileResponse   # <--- Импорт для отдачи файла
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# --- НАСТРОЙКИ ---
DATA_FILE = "data/workouts.json"
if not os.path.exists("data"):
    os.makedirs("data")
API_TOKEN = os.getenv("API_TOKEN", "secret123") 

app = FastAPI(title="TreadLogic API")
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- МОДЕЛИ ---
# (Тут весь твой код моделей Pydantic без изменений...)
# ... WorkoutType, StepType, SegmentType, WorkoutMeta ...
# ... SimpleSegment, ComplexSegment, WorkoutPlan ...
# (Вставь свои модели сюда, чтобы не дублировать текст здесь)
# ------------------

# --- МОДЕЛИ (Копипаст для контекста, если будешь копировать файл целиком) ---
class WorkoutType(str, Enum):
    RECOVERY = "Recovery"
    EASY = "Easy"
    TEMPO = "Tempo"
    INTERVALS = "Intervals"
    LONG_RUN = "LongRun"
    TEST = "Test"

class StepType(str, Enum):
    WARMUP = "warmup"
    WORK = "work"
    REST = "rest"
    COOLDOWN = "cooldown"

class SegmentType(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"

class WorkoutMeta(BaseModel):
    date: str
    title: str
    workout_type: WorkoutType
    description: str
    total_duration_estimate_sec: int
    coach_notes: str
    gear: str
    post_workout_action: Optional[str] = None
    allow_overtime: bool = False

class SimpleSegment(BaseModel):
    segment_type: Literal[SegmentType.SIMPLE] = SegmentType.SIMPLE
    step_type: StepType
    title: str
    duration_sec: int
    speed_kph: float
    incline_percent: float
    notes: Optional[str] = ""

class ComplexSegment(BaseModel):
    segment_type: Literal[SegmentType.COMPLEX] = SegmentType.COMPLEX
    title: str
    repeat_count: int
    skip_last_rest: bool = False
    steps: List[SimpleSegment]

class WorkoutPlan(BaseModel):
    id: str
    meta: WorkoutMeta
    segments: List[Annotated[Union[ComplexSegment, SimpleSegment], Field(discriminator='segment_type')]]


# --- ФУНКЦИИ И ENDPOINTS ---

def load_workouts() -> List[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_workouts(data: List[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

@app.get("/workouts", response_model=List[WorkoutPlan], dependencies=[Security(verify_token)])
def get_workouts():
    return load_workouts()

@app.post("/workouts", response_model=WorkoutPlan, dependencies=[Security(verify_token)])
def add_workout(workout: WorkoutPlan):
    current_data = load_workouts()
    new_workout_dict = workout.model_dump()
    
    index_found = -1
    for i, item in enumerate(current_data):
        if item.get("id") == new_workout_dict["id"]:
            index_found = i
            break
    
    if index_found != -1:
        current_data[index_found] = new_workout_dict
    else:
        current_data.append(new_workout_dict)
    
    save_workouts(current_data)
    return workout

@app.delete("/workouts/{workout_id}", dependencies=[Security(verify_token)])
def delete_workout(workout_id: str):
    current_data = load_workouts()
    new_data = [w for w in current_data if w.get("id") != workout_id]
    if len(new_data) == len(current_data):
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    save_workouts(new_data)
    return {"status": "deleted", "id": workout_id}

# --- ВАЖНО: РАЗДАЧА HTML ---
# Подключаем папку static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/admin", include_in_schema=False)
async def admin_page():
    return FileResponse('static/admin.html')

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse('static/admin.html') # По умолчанию открываем админку