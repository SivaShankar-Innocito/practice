import os
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession # type: ignore
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from sqlalchemy import select
# from dotenv import load_dotenv
from config import Settings

# load_dotenv()
settings = Settings()

class Task(SQLModel, table=True):
    id: int | None = Field(default = None, primary_key = True)
    title: str
    completed: bool = False 

engine = create_async_engine(settings.DATABASE_URL, echo = True)
async_session = sessionmaker(engine, class_ = AsyncSession, expire_on_commit = False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This block runs on startup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Yield control to the application
    yield
    
    # This block runs on shutdown (optional, but good for cleanup)
    print("Application shutting down...")


app = FastAPI(
    title = 'Testing',
    lifespan=lifespan
)

# You'll likely want to add some endpoints here to interact with your database, e.g.:

@app.get("/tasks", response_model=list[Task])
async def get_tasks():
    async with async_session() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return tasks
    
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

@app.post("/tasks", response_model = Task)
async def create_task(task: Task):
    async with async_session() as session:
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, updated_task: Task):
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.title = updated_task.title
        task.completed = updated_task.completed

        await session.commit()
        await session.refresh(task)
        return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await session.delete(task)
        await session.commit()
        return {"message": f"Task {task_id} deleted successfully"}
