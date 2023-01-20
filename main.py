from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import dotenv

# routes
from routes.search import router as search_router
from db.database import engine, SQLModel, Session
from db.models import Search

# Pydantic Models
class SingleCardSearch(BaseModel):
    cardName: str
    websites: list

class BulkCardSearch(BaseModel):
    cardNames: list
    websites: list
    worstCondition: str

class SealedSearch(BaseModel):
    setName: str
    websites: list

class Login(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str
    password: str
    email: str
    user_type: str

# load the differently named dev.env file with dotenv
dotenv.load_dotenv()
app = FastAPI()
app.include_router(search_router, prefix="/search", tags=["search"])

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://snapcasterv2-client.vercel.app",
    "https://snapcaster.bryceeppler.com",
    "https://www.snapcaster.ca",
    "https://snapcaster.ca",
    "http://localhost:3000",
    "https://snapcaster-nextjs.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    return {"message": "Hello World"}