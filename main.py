from sqlalchemy import  String, Integer,select
from sqlalchemy.orm import DeclarativeBase, mapped_column,Mapped
from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine,AsyncSession
from pydantic import BaseModel,Field,EmailStr
from fastapi import FastAPI,Depends
from typing import Annotated

engine = create_async_engine('sqlite+aiosqlite:///users.db',echo=True)
LocalSession = async_sessionmaker(bind=engine)

app = FastAPI()
class Base(DeclarativeBase):
    pass

class UsersModel(Base):
    __tablename__ = 'users'

    id:Mapped[int] = mapped_column(primary_key=True)
    name:Mapped[str] = mapped_column(String(30))
    age:Mapped[int] = mapped_column(Integer)
    email:Mapped[str] = mapped_column(String(30))
    password:Mapped[str] = mapped_column(String)
class UserSchema(BaseModel):
    name: str = Field(max_length=30)
    age: int = Field(ge=10,le=120)
    email: EmailStr
    password: str = Field(min_length=8,max_length=30)


@app.get('/')
async def start_db():
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with LocalSession() as session:
        yield session
SessionDep = Annotated[AsyncSession,Depends(get_db)]
@app.get('/find_user')
async def find_user(email:EmailStr,session:SessionDep):
    stmt = select(UsersModel).where(UsersModel.email == email)
    data = await session.execute(stmt)
    res = data.scalar_one_or_none()
    if res:
        return data.scalar_one_or_none()
    else:
        return {'message': f'User with this email does not exist'}
@app.post('/add_user')
async def add_user(user: UserSchema, session:SessionDep):
    stmt = select(UsersModel).where(UsersModel.email == user.email)
    data = await session.execute(stmt)
    res = data.scalar_one_or_none()

    if res:
        return {'message': 'User with this email is already exists',
                'dataRes':res,
                'data':user}
    else:
        session.add(UsersModel(**user.model_dump()))
        await session.commit()
        await session.close()
        return {'message': 'User added successfully'}
@app.post('/login')
async def login_user( session:SessionDep,user_password:str,user_name:str|None = None):
    stmt = select(UsersModel).where(UsersModel.email == user_name)
    data = await session.execute(stmt)
    res = data.scalar_one_or_none()
    if res:
        stmt_ = select(UsersModel).where(UsersModel.password == user_password)
        data = await session.execute(stmt_)
        res = data.scalar_one_or_none()
        if res:
            return {'message': 'Login Successful',}
        else:
            return {'message': 'Login Failed',}
    else:
        stmt_ = select(UsersModel).where(UsersModel.name == user_name)
        data = await session.execute(stmt_)
        res = data.scalar_one_or_none()
        if res:
            stmt = select(UsersModel).where(UsersModel.password == user_password)
            data = await session.execute(stmt_)
            res = data.scalar_one_or_none()
            if res:
                return {'message': 'Login Successful',}
            else:
                return {'message': 'Login Failed',}
        else:
            return {'message': 'Login Failed',}



