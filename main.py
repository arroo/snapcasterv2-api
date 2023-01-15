from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import dotenv

# routes
from routes.search import router as search_router
from routes.users import router as users_router
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
dotenv.load_dotenv(dotenv_path="dev.env")
app = FastAPI()
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(users_router, prefix="/users", tags=["users"])

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://snapcasterv2-client.vercel.app",
    "https://snapcaster.bryceeppler.com",
    "https://www.snapcaster.ca",
    "https://snapcaster.ca",
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


@app.get("/heatmap/")
async def heatmap():
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    rows = session.query(Search).all()

    results = []
    for row in rows:
        date = row.timestamp[0:10]
        count = 1
        for result in results:
            if result["date"] == date:
                result["count"] += 1
                count = 0
                break
        if count == 1:
            results.append({
                "date": date,
                "count": 1
            })
        
    
    session.close()
    return results
    