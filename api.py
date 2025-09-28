import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional

SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, index=True, nullable=True)
    done = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    done: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None

class TaskInDB(TaskBase):
    id: int

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="API de Lista de Tarefas (To-Do List)",
    description="Uma API simples para gerenciar tarefas usando FastAPI e SQLite.",
    version="1.0.0"
)

@app.get("/", summary="Mensagem de Boas-vindas")
def read_root():
    """
    Endpoint raiz que exibe uma mensagem de boas-vindas.
    """
    return {"message": "Bem-vindo à API de Lista de Tarefas! Acesse /docs para ver a documentação."}

@app.post("/tasks/", response_model=TaskInDB, status_code=status.HTTP_201_CREATED, summary="Criar uma nova tarefa")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova tarefa no banco de dados.

    - **title**: O título da tarefa (obrigatório).
    - **description**: Uma descrição opcional para a tarefa.
    - **done**: Status da tarefa, `false` por padrão.
    """
    db_task = Task(title=task.title, description=task.description, done=task.done)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskInDB], summary="Listar todas as tarefas")
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna uma lista de todas as tarefas cadastradas, com paginação opcional.
    """
    tasks = db.query(Task).offset(skip).limit(limit).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskInDB, summary="Obter uma tarefa específica")
def read_task(task_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de uma tarefa específica pelo seu ID.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return db_task

@app.put("/tasks/{task_id}", response_model=TaskInDB, summary="Atualizar uma tarefa")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    """
    Atualiza uma tarefa existente no banco de dados.
    Você pode enviar apenas os campos que deseja atualizar.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    update_data = task.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir uma tarefa")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Exclui uma tarefa do banco de dados pelo seu ID.
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    db.delete(db_task)
    db.commit()
    return

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
