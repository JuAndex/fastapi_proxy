from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select
import requests


# Define the models
class HeroMissionLink(SQLModel, table=True):
    hero_id: Optional[int] = Field(
        default=None, foreign_key="hero.id", primary_key=True
    )
    mission_id: Optional[int] = Field(
        default=None, foreign_key="mission.id", primary_key=True
    )


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    heroes: list["Hero"] = Relationship(back_populates="team")


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    team: Optional[Team] = Relationship(back_populates="heroes")
    missions: list["Mission"] = Relationship(
        back_populates="heroes", link_model=HeroMissionLink
    )


class Mission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str

    heroes: list[Hero] = Relationship(
        back_populates="missions", link_model=HeroMissionLink
    )


# Setup FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the SQLite database engine
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)


# Dependency: Database session
def get_session():
    with Session(engine) as session:
        yield session


# Create Team
@app.post("/teams/", response_model=Team)
def create_team(team: Team, session: Session = Depends(get_session)):
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


# Create Hero
@app.post("/heroes/", response_model=Hero)
def create_hero(hero: Hero, session: Session = Depends(get_session)):
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


@app.get("/heroes", response_model=list[Hero])
def read_heroes(
    skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
):
    heroes = session.exec(select(Hero).offset(skip).limit(limit)).all()
    return heroes


# Assign Hero to Team
@app.put("/heroes/{hero_id}/team/{team_id}", response_model=Hero)
def assign_hero_to_team(
    hero_id: int, team_id: int, session: Session = Depends(get_session)
):
    hero = session.get(Hero, hero_id)
    team = session.get(Team, team_id)
    if not hero or not team:
        raise HTTPException(status_code=404, detail="Hero or Team not found")
    hero.team_id = team_id
    session.commit()
    session.refresh(hero)
    return hero


# Create Mission
@app.post("/missions/", response_model=Mission)
def create_mission(mission: Mission, session: Session = Depends(get_session)):
    session.add(mission)
    session.commit()
    session.refresh(mission)
    return mission


# Assign Hero to Mission (Many-to-Many)
@app.put("/missions/{mission_id}/heroes/{hero_id}", response_model=Mission)
def assign_hero_to_mission(
    mission_id: int, hero_id: int, session: Session = Depends(get_session)
):
    hero = session.get(Hero, hero_id)
    mission = session.get(Mission, mission_id)
    if not hero or not mission:
        raise HTTPException(status_code=404, detail="Hero or Mission not found")
    hero_mission_link = HeroMissionLink(hero_id=hero_id, mission_id=mission_id)
    session.add(hero_mission_link)
    session.commit()
    return mission


# Read Hero with relationships
@app.get("/heroes/{hero_id}", response_model=Hero)
def read_hero(hero_id: int, session: Session = Depends(get_session)):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


# Read Team with Heroes
@app.get("/teams/{team_id}", response_model=Team)
def read_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# Read Mission with Heroes
@app.get("/missions/{mission_id}", response_model=Mission)
def read_mission(mission_id: int, session: Session = Depends(get_session)):
    mission = session.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


BACKEND_URL = "https://jsonplaceholder.typicode.com"
cookie = "1234"


@app.api_route(
    "/{path_name:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def catch_all(request: Request, path_name: str):
    url = f"{BACKEND_URL}/{path_name}"

    response = requests.request(
        method=request.method,
        url=url,
        params=request.query_params,
        data=await request.body(),
        allow_redirects=False,
        # proxies=proxies,
        verify=False,
        cookies={"ebizaauth": cookie},
        headers={
            "Accept": "application/json;charset=UTF-8",
        },
    )

    proxy_response = Response(response.content, status_code=response.status_code)
    for name, value in response.headers.items():
        if name.lower() not in ["content-encoding", "transfer-encoding", "connection"]:
            proxy_response.headers[name] = value

    return proxy_response


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
