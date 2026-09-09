# import secrets
# from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from jose import JWTError, jwt
# from datetime import datetime, timedelta
# from argon2 import PasswordHasher
# from argon2.exceptions import VerifyMismatchError
# from sqlalchemy import desc
# from typing import Optional
# from pydantic import BaseModel
# import os
# import requests

# from dotenv import load_dotenv
# load_dotenv()

# import secrets
# from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
# from websocket_manager import manager
# from database import SessionLocal, engine
# from models import Base, User, Project, Task, Team, TeamMember, Message, InviteToken, InviteToken, InviteToken, InviteToken, InviteToken, InviteToken, InviteToken, InviteToken, InviteToken
# from schemas import UserCreate, ProjectCreate, TaskCreate, TeamCreate, AddMemberRequest
# from services.analytics_engine import calculate_tpi
# from services.ml_engine import (
#     predict_task_delay,
#     predict_productivity,
#     recommend_assignee,
#     get_model_info
# )
# # ==========================================
# # CONFIG
# # ==========================================

# SECRET_KEY = "supersecretkey_change_this_in_production"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# ph = PasswordHasher()

# # ==========================================
# # HELPERS
# # ==========================================

# def hash_password(password: str):
#     return ph.hash(password)

# def verify_password(plain_password: str, hashed_password: str):
#     try:
#         ph.verify(hashed_password, plain_password)
#         return True
#     except VerifyMismatchError:
#         return False

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     user = db.query(User).filter(User.id == int(user_id)).first()
#     if user is None:
#         raise credentials_exception
#     return user

# def get_team_member_role(team_id: int, user_id: int, db: Session):
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == user_id
#     ).first()
#     return membership.role if membership else None

# def require_team_role(team_id: int, user_id: int, allowed_roles: list, db: Session):
#     role = get_team_member_role(team_id, user_id, db)
#     if role not in allowed_roles:
#         raise HTTPException(status_code=403, detail="You don't have permission for this action")

# # ==========================================
# # APP
# # ==========================================

# app = FastAPI()
# @app.post("/teams/{team_id}/invite")
# def generate_invite(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     require_team_role(team_id, current_user.id, ["admin"], db)
#     token = secrets.token_urlsafe(16)
#     invite = InviteToken(token=token, team_id=team_id)
#     db.add(invite)
#     db.commit()
#     return {"invite_token": token}

# @app.post("/teams/join/{token}")
# def join_via_invite(
#     token: str,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     invite = db.query(InviteToken).filter(InviteToken.token == token).first()
#     if not invite:
#         raise HTTPException(status_code=404, detail="Invalid or expired invite link")
#     existing = db.query(TeamMember).filter(
#         TeamMember.team_id == invite.team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Already a member of this team")
#     new_member = TeamMember(team_id=invite.team_id, user_id=current_user.id, role="member")
#     db.add(new_member)
#     db.commit()
#     team = db.query(Team).filter(Team.id == invite.team_id).first()
#     return {"message": "Joined successfully", "team_id": invite.team_id, "team_name": team.name if team else ""}

# app.add_middleware(
#     CORSMiddleware,
#    allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# @app.on_event("startup")
# def startup():
#     print("Creating tables...")
#     Base.metadata.create_all(bind=engine)
#     print("Tables created.")

# @app.get("/")
# def root():
#     return {"status": "TeamPulse backend running"}

# # ==========================================
# # AUTH
# # ==========================================

# @app.post("/register")
# def register(user: UserCreate, db: Session = Depends(get_db)):
#     existing = db.query(User).filter(User.email == user.email).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     new_user = User(
#         name=user.name,
#         email=user.email,
#         password=hash_password(user.password),
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     token = create_access_token({"sub": str(new_user.id)})
#     return {
#         "access_token": token,
#         "token_type": "bearer",
#         "user_id": new_user.id,
#         "name": new_user.name,
#         "email": new_user.email
#     }

# @app.post("/login")
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == form_data.username).first()
#     if not user or not verify_password(form_data.password, user.password):
#         raise HTTPException(status_code=400, detail="Invalid email or password")
#     token = create_access_token({"sub": str(user.id)})
#     return {
#         "access_token": token,
#         "token_type": "bearer",
#         "user_id": user.id,
#         "name": user.name,
#         "email": user.email
#     }

# class GoogleLoginRequest(BaseModel):
#     code: str
# @app.post("/auth/google")
# def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
#     try:
#         google_client_id = os.getenv("GOOGLE_CLIENT_ID")
#         google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
#         google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

#         print("REDIRECT_URI =", os.getenv("GOOGLE_REDIRECT_URI"))


    
#         if not google_client_id or not google_client_secret or not google_redirect_uri:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Google OAuth environment variables are missing"
#             )

#         token_res = requests.post(
#             "https://oauth2.googleapis.com/token",
#             data={
#                 "code": payload.code,
#                 "client_id": google_client_id,
#                 "client_secret": google_client_secret,
#                 "redirect_uri": google_redirect_uri,
#                 "grant_type": "authorization_code",
#             },
#             timeout=15,
#         )

#         token_json = token_res.json()
#         print("GOOGLE TOKEN RESPONSE:", token_json)

#         access_token = token_json.get("access_token")
#         if not access_token:
#             raise HTTPException(
#                 status_code=400,
#                 detail=token_json.get("error_description")
#                 or token_json.get("error")
#                 or "Failed to get Google access token"
#             )

#         userinfo_res = requests.get(
#             "https://www.googleapis.com/oauth2/v2/userinfo",
#             headers={"Authorization": f"Bearer {access_token}"},
#             timeout=15,
#         )

#         userinfo = userinfo_res.json()
#         print("GOOGLE USERINFO:", userinfo)

#         email = userinfo.get("email")
#         if not email:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"No email found in Google response: {userinfo}"
#             )

#         name = userinfo.get("name") or email.split("@")[0]

#         user = db.query(User).filter(User.email == email).first()
#         if not user:
#             user = User(
#                 name=name,
#                 email=email,
#                 password=hash_password(secrets.token_hex(16)),
#             )
#             db.add(user)
#             db.commit()
#             db.refresh(user)

#         app_token = create_access_token({"sub": str(user.id)})

#         return {
#             "access_token": app_token,
#             "token_type": "bearer",
#             "user_id": user.id,
#             "name": user.name,
#             "email": user.email,
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         print("GOOGLE ERROR:", str(e))
#         raise HTTPException(status_code=400, detail=str(e))
# @app.get("/notifications")
# def get_notifications(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     notifs = []
#     week_ago = datetime.utcnow() - timedelta(days=7)

#     # Recently assigned tasks
#     assigned_tasks = (
#         db.query(Task)
#         .filter(Task.assigned_user_id == current_user.id)
#         .filter(Task.created_at >= week_ago)
#         .order_by(Task.created_at.desc())
#         .limit(5)
#         .all()
#     )
#     for t in assigned_tasks:
#         notifs.append({
#             "id":      f"task_{t.id}",
#             "type":    "task_assigned",
#             "title":   "Task Assigned",
#             "message": f'"{t.title}" was assigned to you',
#             "time":    t.created_at.isoformat() if t.created_at else None,
#             "read":    False,
#         })

#     # Recently completed tasks
#     completed = (
#         db.query(Task)
#         .filter(Task.assigned_user_id == current_user.id, Task.status == "DONE")
#         .order_by(Task.completed_at.desc())
#         .limit(3)
#         .all()
#     )
#     for t in completed:
#         notifs.append({
#             "id":      f"done_{t.id}",
#             "type":    "task_completed",
#             "title":   "Task Completed",
#             "message": f'You completed "{t.title}" — +20 pts',
#             "time":    t.completed_at.isoformat() if t.completed_at else None,
#             "read":    True,
#         })

#     notifs = sorted(notifs, key=lambda x: x["time"] or "", reverse=True)[:10]
#     return {
#         "notifications": notifs,
#         "unread_count":  sum(1 for n in notifs if not n["read"]),
#     }

# # ==========================================
# # USER SETTINGS
# # ==========================================

# @app.get("/user/settings")
# def get_user_settings(current_user: User = Depends(get_current_user)):
#     return {
#         "id":       current_user.id,
#         "name":     current_user.name,
#         "email":    current_user.email,
#         "role":     getattr(current_user, "role",     "") or "",
#         "bio":      getattr(current_user, "bio",      "") or "",
#         "phone":    getattr(current_user, "phone",    "") or "",
#         "location": getattr(current_user, "location", "") or "",
#         "points":   getattr(current_user, "points",   0),
#         "level":    getattr(current_user, "level",    1),
#         "streak":   getattr(current_user, "streak",   0),
#     }

# @app.put("/user/settings")
# def update_user_settings(
#     data: dict,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     profile = data.get("profile", data)  # support both {profile:{}} and flat {}
#     for field in ["name", "email", "role", "bio", "phone", "location"]:
#         val = profile.get(field)
#         if val is not None and hasattr(current_user, field):
#             setattr(current_user, field, val)
#     db.commit()
#     db.refresh(current_user)
#     return {"message": "Settings updated", "name": current_user.name, "email": current_user.email}

# @app.put("/user/password")
# def change_password(
#     payload: dict,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     if not verify_password(payload.get("currentPassword", ""), current_user.password):
#         raise HTTPException(status_code=400, detail="Current password is incorrect")
#     current_user.password = hash_password(payload.get("newPassword", ""))
#     db.commit()
#     return {"message": "Password changed successfully"}

# # ==========================================
# # USER SEARCH
# # ==========================================

# @app.get("/users/search")
# def search_user(
#     email: str,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {"id": user.id, "name": user.name, "email": user.email}

# # ==========================================
# # TEAM ROUTES
# # ==========================================

# @app.post("/teams")
# def create_team(
#     team: TeamCreate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     new_team = Team(name=team.name, created_by=current_user.id)
#     db.add(new_team)
#     db.commit()
#     db.refresh(new_team)
#     member = TeamMember(team_id=new_team.id, user_id=current_user.id, role="admin")
#     db.add(member)
#     db.commit()
#     return {"message": "Team created", "team_id": new_team.id}

# @app.get("/teams")
# def get_teams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
#     ids = [m.team_id for m in memberships]
#     return db.query(Team).filter(Team.id.in_(ids)).all()

# @app.get("/teams/{team_id}/my-role")
# def get_my_role(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if not membership:
#         raise HTTPException(status_code=404, detail="Not a member")
#     return {"role": membership.role}

# @app.get("/teams/{team_id}/members")
# def get_team_members(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if not membership:
#         raise HTTPException(status_code=403, detail="Not a member of this team")

#     members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
#     return [
#         {
#             "user_id":         m.user_id,
#             "name":            m.user.name,
#             "email":           m.user.email,
#             "role":            m.role,
#             "joined_at":       m.joined_at.isoformat() if m.joined_at else None,
#             "points":          getattr(m.user, "points",          0),
#             "level":           getattr(m.user, "level",           1),
#             "streak":          getattr(m.user, "streak",          0),
#             "total_completed": getattr(m.user, "total_completed", 0),
#         }
#         for m in members
#     ]

# @app.post("/teams/{team_id}/add-member")
# def add_member(
#     team_id: int,
#     request: AddMemberRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     require_team_role(team_id, current_user.id, ["admin"], db)
#     user = db.query(User).filter(User.id == request.user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     existing = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == request.user_id
#     ).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="User already in team")
#     new_member = TeamMember(team_id=team_id, user_id=request.user_id, role="member")
#     db.add(new_member)
#     db.commit()
#     return {"message": "Member added successfully"}

# @app.delete("/teams/{team_id}/members/{user_id}")
# def remove_member(
#     team_id: int,
#     user_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     require_team_role(team_id, current_user.id, ["admin"], db)
#     if user_id == current_user.id:
#         raise HTTPException(status_code=400, detail="Use /leave to remove yourself")
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == user_id
#     ).first()
#     if not membership:
#         raise HTTPException(status_code=404, detail="Member not found")
#     db.delete(membership)
#     db.commit()
#     return {"message": "Member removed successfully"}

# @app.delete("/teams/{team_id}")
# def delete_team(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     require_team_role(team_id, current_user.id, ["admin"], db)
#     db.query(TeamMember).filter(TeamMember.team_id == team_id).delete()
#     db.query(Team).filter(Team.id == team_id).delete()
#     db.commit()
#     return {"message": "Team deleted"}

# @app.post("/teams/{team_id}/leave")
# def leave_team(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if not membership:
#         raise HTTPException(status_code=404, detail="Not a member")
#     if membership.role == "admin":
#         raise HTTPException(status_code=400, detail="Admin cannot leave. Delete the team instead.")
#     db.delete(membership)
#     db.commit()
#     return {"message": "Left team"}

# @app.post("/teams/{team_id}/invite")
# def generate_invite(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     require_team_role(team_id, current_user.id, ["admin"], db)
#     token = secrets.token_urlsafe(16)
#     invite_tokens[token] = team_id
#     return {"invite_token": token}

# @app.post("/teams/join/{token}")
# def join_via_invite(
#     token: str,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     team_id = invite_tokens.get(token)
#     if not team_id:
#         raise HTTPException(status_code=404, detail="Invalid or expired invite link")
#     existing = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Already a member of this team")
#     new_member = TeamMember(team_id=team_id, user_id=current_user.id, role="member")
#     db.add(new_member)
#     db.commit()
#     team = db.query(Team).filter(Team.id == team_id).first()
#     return {"message": "Joined team successfully", "team_id": team_id, "team_name": team.name if team else ""}

# # ==========================================
# # PROJECT ROUTES
# # ==========================================

# @app.post("/projects")
# def create_project(
#     project: ProjectCreate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     role = get_team_member_role(project.team_id, current_user.id, db)
#     if role is None:
#         raise HTTPException(status_code=403, detail="Not a member of this team")
#     new_project = Project(name=project.name, owner_id=current_user.id, team_id=project.team_id)
#     db.add(new_project)
#     db.commit()
#     db.refresh(new_project)
#     return {"message": "Project created", "project_id": new_project.id}

# @app.get("/projects/team/{team_id}")
# def get_projects_by_team(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     return db.query(Project).filter(Project.team_id == team_id).all()

# @app.get("/projects")
# def get_all_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     return db.query(Project).all()

# # ==========================================
# # TASK ROUTES
# # ==========================================

# @app.post("/tasks")
# def create_task(task: TaskCreate, db: Session = Depends(get_db)):
#     project = db.query(Project).filter(Project.id == task.project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
#     user = db.query(User).filter(User.id == task.assigned_user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="Assigned user not found")
#     new_task = Task(
#         title=task.title,
#         status="TODO",
#         project_id=task.project_id,
#         assigned_user_id=task.assigned_user_id,
#         complexity_score=task.complexity_score,
#         deadline=task.deadline
#     )
#     db.add(new_task)
#     db.commit()
#     db.refresh(new_task)
#     return {"message": "Task created", "task_id": new_task.id}

# @app.put("/tasks/{task_id}/complete")
# def complete_task(task_id: int, db: Session = Depends(get_db)):
#     task = db.query(Task).filter(Task.id == task_id).first()
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
#     task.status = "DONE"
#     task.completed_at = datetime.utcnow()
#     user = db.query(User).filter(User.id == task.assigned_user_id).first()
#     if user:
#         user.points = (user.points or 0) + 20
#         user.level = (user.points // 200) + 1
#         user.total_completed = (user.total_completed or 0) + 1
#     db.commit()
#     return {
#         "message": "Task completed",
#         "points": user.points if user else 0,
#         "level":  user.level  if user else 1
#     }

# @app.put("/tasks/{task_id}")
# def update_task(
#     task_id: int,
#     updates: dict,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     task = db.query(Task).filter(Task.id == task_id).first()
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
#     if "status" in updates:
#         task.status = updates["status"]
#         if updates["status"] == "DONE":
#             task.completed_at = datetime.utcnow()
#         else:
#             task.completed_at = None
#     for field in ["title", "deadline", "complexity_score", "assigned_user_id"]:
#         if field in updates:
#             setattr(task, field, updates[field])
#     db.commit()
#     db.refresh(task)
#     return {"message": "Task updated", "task_id": task.id}

# @app.delete("/tasks/{task_id}")
# def delete_task(
#     task_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     task = db.query(Task).filter(Task.id == task_id).first()
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
#     db.delete(task)
#     db.commit()
#     return {"message": "Task deleted"}

# @app.get("/projects/{project_id}/tasks")
# def get_project_tasks(
#     project_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     project = db.query(Project).filter(Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
#     tasks = db.query(Task).filter(Task.project_id == project_id).all()
#     return [
#         {
#             "id":               t.id,
#             "title":            t.title,
#             "status":           t.status,
#             "project_id":       t.project_id,
#             "assigned_user_id": t.assigned_user_id,
#             "complexity_score": t.complexity_score,
#             "created_at":       t.created_at.isoformat() if t.created_at else None,
#             "deadline":         t.deadline.isoformat()   if t.deadline   else None,
#             "completed_at":     t.completed_at.isoformat() if t.completed_at else None,
#             "assigned_user": {
#                 "id":   t.assigned_user.id,
#                 "name": t.assigned_user.name,
#             } if t.assigned_user else None,
#         }
#         for t in tasks
#     ]

# # ==========================================
# # ANALYTICS
# # ==========================================

# @app.get("/analytics/team/{team_id}")
# def get_team_analytics(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if not membership:
#         raise HTTPException(status_code=403, detail="Not a member of this team")

#     projects    = db.query(Project).filter(Project.team_id == team_id).all()
#     project_ids = [p.id for p in projects]
#     tasks       = db.query(Task).filter(Task.project_id.in_(project_ids)).all() if project_ids else []
#     total       = len(tasks)

#     if total == 0:
#         return {"team_completion_rate": 0, "team_overdue_rate": 0, "team_tpi_score": 0}

#     completed   = len([t for t in tasks if t.status == "DONE"])
#     overdue     = len([t for t in tasks if t.deadline and t.completed_at and t.completed_at > t.deadline])
#     comp_rate   = completed / total
#     overdue_rate= overdue / total
#     tpi         = calculate_tpi(comp_rate, 1 - overdue_rate, 0)

#     return {
#         "team_completion_rate": round(comp_rate * 100, 2),
#         "team_overdue_rate":    round(overdue_rate * 100, 2),
#         "team_tpi_score":       tpi
#     }

# # ==========================================
# # DASHBOARD
# # ==========================================

# @app.get("/dashboard/{team_id}")
# def get_dashboard(
#     team_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if not membership:
#         raise HTTPException(status_code=403, detail="Not a member of this team")

#     projects    = db.query(Project).filter(Project.team_id == team_id).all()
#     project_ids = [p.id for p in projects]
#     all_tasks   = db.query(Task).filter(Task.project_id.in_(project_ids)).all() if project_ids else []

#     now             = datetime.utcnow()
#     total_tasks     = len(all_tasks)
#     completed_tasks = len([t for t in all_tasks if t.status == "DONE"])
#     in_progress     = len([t for t in all_tasks if t.status == "IN_PROGRESS"])
#     todo_tasks      = len([t for t in all_tasks if t.status == "TODO"])
#     overdue_tasks   = len([t for t in all_tasks if t.status != "DONE" and t.deadline and t.deadline < now])
#     completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)

#     # TPI
#     overdue_rate = overdue_tasks / total_tasks if total_tasks > 0 else 0
#     tpi = calculate_tpi(completion_rate / 100, 1 - overdue_rate, 0) if total_tasks > 0 else 0

#     # Risk
#     if total_tasks == 0:
#         risk_level, risk_reason = "No Data", "No tasks yet. Add tasks to generate insights."
#     elif tpi >= 80:
#         risk_level, risk_reason = "Low Risk", "Team performance is excellent. Keep it up!"
#     elif tpi >= 50:
#         risk_level, risk_reason = "Moderate Risk", f"{overdue_tasks} tasks overdue. Monitor closely."
#     else:
#         risk_level, risk_reason = "High Risk", f"High overdue rate. Immediate action needed."

#     # My tasks
#     my_tasks     = [t for t in all_tasks if t.assigned_user_id == current_user.id]
#     my_completed = len([t for t in my_tasks if t.status == "DONE"])
#     my_overdue   = len([t for t in my_tasks if t.status != "DONE" and t.deadline and t.deadline < now])

#     # Members leaderboard
#     members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
#     member_stats = []
#     for m in members:
#         u = m.user
#         u_tasks     = [t for t in all_tasks if t.assigned_user_id == u.id]
#         u_completed = len([t for t in u_tasks if t.status == "DONE"])
#         member_stats.append({
#             "user_id":         u.id,
#             "name":            u.name,
#             "points":          getattr(u, "points", 0),
#             "level":           getattr(u, "level",  1),
#             "streak":          getattr(u, "streak", 0),
#             "tasks_completed": u_completed,
#             "total_tasks":     len(u_tasks),
#         })
#     member_stats.sort(key=lambda x: x["points"], reverse=True)

#     # Recent activity
#     recent = sorted(
#         [t for t in all_tasks if t.status == "DONE"],
#         key=lambda t: t.completed_at or t.created_at or now,
#         reverse=True
#     )[:5]

#     recent_tasks = []
#     for t in recent:
#         assignee = db.query(User).filter(User.id == t.assigned_user_id).first()
#         recent_tasks.append({
#             "id":       t.id,
#             "title":    t.title,
#             "status":   t.status,
#             "deadline": t.deadline.isoformat() if t.deadline else None,
#             "assignee": assignee.name if assignee else "Unassigned",
#         })

#     # Projects summary
#     projects_summary = []
#     for p in projects:
#         p_tasks   = [t for t in all_tasks if t.project_id == p.id]
#         p_done    = len([t for t in p_tasks if t.status == "DONE"])
#         p_total   = len(p_tasks)
#         p_overdue = len([t for t in p_tasks if t.status != "DONE" and t.deadline and t.deadline < now])
#         projects_summary.append({
#             "id":              p.id,
#             "name":            p.name,
#             "total_tasks":     p_total,
#             "completed_tasks": p_done,
#             "overdue_tasks":   p_overdue,
#             "completion_rate": round((p_done / p_total * 100) if p_total > 0 else 0),
#         })

#     return {
#         "team_id":         team_id,
#         "total_projects":  len(projects),
#         "total_tasks":     total_tasks,
#         "completed_tasks": completed_tasks,
#         "in_progress":     in_progress,
#         "todo_tasks":      todo_tasks,
#         "overdue_tasks":   overdue_tasks,
#         "completion_rate": completion_rate,
#         "tpi_score":       round(tpi, 1),
#         "sprint_progress": completion_rate,
#         "risk_level":      risk_level,
#         "risk_reason":     risk_reason,
#         "my_tasks": {
#             "total":     len(my_tasks),
#             "completed": my_completed,
#             "overdue":   my_overdue,
#         },
#         "members":         member_stats,
#         "recent_tasks":    recent_tasks,
#         "projects":        projects_summary,
#         "user": {
#             "id":              current_user.id,
#             "name":            current_user.name,
#             "points":          getattr(current_user, "points",          0),
#             "level":           getattr(current_user, "level",           1),
#             "streak":          getattr(current_user, "streak",          0),
#             "total_completed": getattr(current_user, "total_completed", 0),
#         }
#     }

# # ==========================================
# # WEBSOCKET CHAT
# # ==========================================

# @app.websocket("/ws/chat/{team_id}")
# async def websocket_chat(
#     websocket: WebSocket,
#     team_id: int,
#     token: str = Query(...)
# ):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = int(payload.get("sub"))
#     except Exception:
#         await websocket.close(code=1008)
#         return

#     db   = SessionLocal()
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         await websocket.close(code=1008)
#         db.close()
#         return

#     await manager.connect(websocket, team_id, user_id, user.name)

#     try:
#         while True:
#             data = await websocket.receive_json()
#             msg_type = data.get("type")

#             if msg_type == "message":
#                 new_msg = Message(
#                     team_id=team_id,
#                     user_id=user_id,
#                     content=data.get("content"),
#                     timestamp=datetime.utcnow()
#                 )
#                 db.add(new_msg)
#                 db.commit()
#                 db.refresh(new_msg)
#                 await manager.broadcast_to_team(team_id, {
#                     "type":       "message",
#                     "message_id": new_msg.id,
#                     "user_id":    user_id,
#                     "username":   user.name,
#                     "content":    data.get("content"),
#                     "timestamp":  new_msg.timestamp.isoformat()
#                 })
#             elif msg_type == "typing":
#                 await manager.send_typing_indicator(team_id, user_id, user.name, data.get("is_typing", False))

#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#     finally:
#         db.close()

# # ==========================================
# # CHAT HISTORY
# # ==========================================

# @app.get("/teams/{team_id}/messages")
# def get_team_messages(
#     team_id: int,
#     limit: int = 50,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     membership = db.query(TeamMember).filter(
#         TeamMember.team_id == team_id,
#         TeamMember.user_id == current_user.id
#     ).first()
#     if not membership:
#         raise HTTPException(status_code=403, detail="Not a member of this team")

#     messages = db.query(Message).filter(Message.team_id == team_id)\
#         .order_by(desc(Message.timestamp)).limit(limit).all()

#     return [
#         {
#             "id":        m.id,
#             "user_id":   m.user_id,
#             "username":  m.user.name,
#             "content":   m.content,
#             "timestamp": m.timestamp.isoformat()
#         }
#         for m in reversed(messages)
#     ]



import secrets
import os
import requests

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import desc
from typing import Optional
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from websocket_manager import manager
from database import SessionLocal, engine
from models import Base, User, Project, Task, Team, TeamMember, Message, InviteToken
from schemas import UserCreate, ProjectCreate, TaskCreate, TeamCreate, AddMemberRequest
from services.analytics_engine import calculate_tpi
from services.ml_engine import (
    predict_task_delay,
    predict_productivity,
    recommend_assignee,
    get_model_info
)

# ==========================================
# CONFIG
# ==========================================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "supersecretkey_change_this_in_production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
ph = PasswordHasher()

# ==========================================
# HELPERS
# ==========================================

def hash_password(password: str):
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def get_team_member_role(team_id: int, user_id: int, db: Session):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    return membership.role if membership else None

def require_team_role(team_id: int, user_id: int, allowed_roles: list, db: Session):
    role = get_team_member_role(team_id, user_id, db)
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail="You don't have permission for this action")

# ==========================================
# APP
# ==========================================

app = FastAPI()

@app.middleware("http")
async def add_coop_header(request, call_next):
    response = await call_next(request)

    response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
    response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    import time
    from sqlalchemy.exc import OperationalError

    print("Creating tables...")
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            print("Tables created.")
            break
        except OperationalError as e:
            if attempt == max_retries:
                print(f"DB connection failed after {max_retries} attempts, giving up: {e}")
                raise
            wait = attempt * 3  # 3s, 6s, 9s, 12s...
            print(f"DB connection attempt {attempt} failed, retrying in {wait}s...")
            time.sleep(wait)

@app.get("/")
def root():
    return {"status": "TeamPulse backend running"}

# ==========================================
# AUTH
# ==========================================

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_access_token({"sub": str(new_user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email
    }

class GoogleLoginRequest(BaseModel):
    code: str

@app.post("/auth/google")
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        google_client_id     = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        google_redirect_uri  = os.getenv("GOOGLE_REDIRECT_URI")

        if not google_client_id or not google_client_secret or not google_redirect_uri:
            raise HTTPException(status_code=500, detail="Google OAuth environment variables are missing")

        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": payload.code,
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "redirect_uri": google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        token_json   = token_res.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail=token_json.get("error_description") or "Failed to get Google access token")

        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        ).json()

        email = userinfo.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="No email found in Google response")

        name = userinfo.get("name") or email.split("@")[0]
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name=name, email=email, password=hash_password(secrets.token_hex(16)))
            db.add(user)
            db.commit()
            db.refresh(user)

        app_token = create_access_token({"sub": str(user.id)})
        return {"access_token": app_token, "token_type": "bearer", "user_id": user.id, "name": user.name, "email": user.email}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# NOTIFICATIONS
# ==========================================

@app.get("/notifications")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs   = []
    week_ago = datetime.utcnow() - timedelta(days=7)

    assigned_tasks = (
        db.query(Task)
        .filter(Task.assigned_user_id == current_user.id)
        .filter(Task.created_at >= week_ago)
        .order_by(Task.created_at.desc())
        .limit(5)
        .all()
    )
    for t in assigned_tasks:
        notifs.append({
            "id":      f"task_{t.id}",
            "type":    "task_assigned",
            "title":   "Task Assigned",
            "message": f'"{t.title}" was assigned to you',
            "time":    t.created_at.isoformat() if t.created_at else None,
            "read":    False,
        })

    completed = (
        db.query(Task)
        .filter(Task.assigned_user_id == current_user.id, Task.status == "DONE")
        .order_by(Task.completed_at.desc())
        .limit(3)
        .all()
    )
    for t in completed:
        notifs.append({
            "id":      f"done_{t.id}",
            "type":    "task_completed",
            "title":   "Task Completed",
            "message": f'You completed "{t.title}" — +20 pts',
            "time":    t.completed_at.isoformat() if t.completed_at else None,
            "read":    True,
        })

    notifs = sorted(notifs, key=lambda x: x["time"] or "", reverse=True)[:10]
    return {
        "notifications": notifs,
        "unread_count":  sum(1 for n in notifs if not n["read"]),
    }

# ==========================================
# USER SETTINGS
# ==========================================

@app.get("/user/settings")
def get_user_settings(current_user: User = Depends(get_current_user)):
    return {
        "id":       current_user.id,
        "name":     current_user.name,
        "email":    current_user.email,
        "role":     getattr(current_user, "role",     "") or "",
        "bio":      getattr(current_user, "bio",      "") or "",
        "phone":    getattr(current_user, "phone",    "") or "",
        "location": getattr(current_user, "location", "") or "",
        "points":   getattr(current_user, "points",   0),
        "level":    getattr(current_user, "level",    1),
        "streak":   getattr(current_user, "streak",   0),
    }

@app.put("/user/settings")
def update_user_settings(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = data.get("profile", data)
    for field in ["name", "email", "role", "bio", "phone", "location"]:
        val = profile.get(field)
        if val is not None and hasattr(current_user, field):
            setattr(current_user, field, val)
    db.commit()
    db.refresh(current_user)
    return {"message": "Settings updated", "name": current_user.name, "email": current_user.email}

@app.put("/user/password")
def change_password(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.get("currentPassword", ""), current_user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password = hash_password(payload.get("newPassword", ""))
    db.commit()
    return {"message": "Password changed successfully"}

# ==========================================
# USER SEARCH
# ==========================================

@app.get("/users/search")
def search_user(
    email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "email": user.email}

# ==========================================
# TEAM ROUTES
# ==========================================

@app.post("/teams")
def create_team(
    team: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_team = Team(name=team.name, created_by=current_user.id)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    member = TeamMember(team_id=new_team.id, user_id=current_user.id, role="admin")
    db.add(member)
    db.commit()
    return {"message": "Team created", "team_id": new_team.id}

@app.get("/teams")
def get_teams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    ids = [m.team_id for m in memberships]
    return db.query(Team).filter(Team.id.in_(ids)).all()

@app.get("/teams/{team_id}/my-role")
def get_my_role(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member")
    return {"role": membership.role}

@app.get("/teams/{team_id}/members")
def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    return [
        {
            "user_id":         m.user_id,
            "name":            m.user.name,
            "email":           m.user.email,
            "role":            m.role,
            "joined_at":       m.joined_at.isoformat() if m.joined_at else None,
            "points":          getattr(m.user, "points",          0),
            "level":           getattr(m.user, "level",           1),
            "streak":          getattr(m.user, "streak",          0),
            "total_completed": getattr(m.user, "total_completed", 0),
        }
        for m in members
    ]

@app.post("/teams/{team_id}/add-member")
def add_member(
    team_id: int,
    request: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_team_role(team_id, current_user.id, ["admin"], db)
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == request.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already in team")
    new_member = TeamMember(team_id=team_id, user_id=request.user_id, role="member")
    db.add(new_member)
    db.commit()
    return {"message": "Member added successfully"}

@app.delete("/teams/{team_id}/members/{user_id}")
def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_team_role(team_id, current_user.id, ["admin"], db)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Use /leave to remove yourself")
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(membership)
    db.commit()
    return {"message": "Member removed successfully"}

@app.delete("/teams/{team_id}")
def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_team_role(team_id, current_user.id, ["admin"], db)

    # Step 1 — delete invite tokens
    db.query(InviteToken).filter(InviteToken.team_id == team_id).delete()

    # Step 2 — delete all messages
    db.query(Message).filter(Message.team_id == team_id).delete()

    # Step 3 — delete tasks inside projects
    projects = db.query(Project).filter(Project.team_id == team_id).all()
    for project in projects:
        db.query(Task).filter(Task.project_id == project.id).delete()

    # Step 4 — delete projects
    db.query(Project).filter(Project.team_id == team_id).delete()

    # Step 5 — delete members
    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete()

    # Step 6 — delete team
    db.query(Team).filter(Team.id == team_id).delete()

    db.commit()
    return {"message": "Team deleted"}
@app.post("/teams/{team_id}/leave")
def leave_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member")
    if membership.role == "admin":
        raise HTTPException(status_code=400, detail="Admin cannot leave. Delete the team instead.")
    db.delete(membership)
    db.commit()
    return {"message": "Left team"}

# ✅ FIX: Invite stored in DB (not in-memory dict that resets on restart)
@app.post("/teams/{team_id}/invite")
def generate_invite(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_team_role(team_id, current_user.id, ["admin"], db)
    token = secrets.token_urlsafe(16)
    invite = InviteToken(token=token, team_id=team_id)
    db.add(invite)
    db.commit()
    return {"invite_token": token}

@app.post("/teams/join/{token}")
def join_via_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invite = db.query(InviteToken).filter(InviteToken.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invite link")
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == invite.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this team")
    new_member = TeamMember(team_id=invite.team_id, user_id=current_user.id, role="member")
    db.add(new_member)
    db.commit()
    team = db.query(Team).filter(Team.id == invite.team_id).first()
    return {"message": "Joined team successfully", "team_id": invite.team_id, "team_name": team.name if team else ""}

# ==========================================
# PROJECT ROUTES
# ==========================================

@app.post("/projects")
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = get_team_member_role(project.team_id, current_user.id, db)
    if role is None:
        raise HTTPException(status_code=403, detail="Not a member of this team")
    new_project = Project(name=project.name, owner_id=current_user.id, team_id=project.team_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"message": "Project created", "project_id": new_project.id}

@app.get("/projects/team/{team_id}")
def get_projects_by_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(Project.team_id == team_id).all()
    now = datetime.utcnow()
    result = []
    for p in projects:
        total   = len(p.tasks)
        done    = len([t for t in p.tasks if t.status == "DONE"])
        overdue = len([t for t in p.tasks if t.status != "DONE" and t.deadline and t.deadline < now])
        result.append({
            "id":              p.id,
            "name":            p.name,
            "team_id":         p.team_id,
            "status":          "In Progress" if total > 0 else "Not Started",
            "completion_rate": round((done / total * 100) if total > 0 else 0),
            "total_tasks":     total,
            "overdue_tasks":   overdue,
        })
    return result

# ✅ FIX: Added missing GET /projects/{project_id} endpoint (caused blank project detail page)
@app.get("/projects/{project_id}")
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    now     = datetime.utcnow()
    total   = len(project.tasks)
    done    = len([t for t in project.tasks if t.status == "DONE"])
    overdue = len([t for t in project.tasks if t.status != "DONE" and t.deadline and t.deadline < now])
    return {
        "id":              project.id,
        "name":            project.name,
        "team_id":         project.team_id,
        "owner_id":        project.owner_id,
        "status":          "In Progress" if total > 0 else "Not Started",
        "completion_rate": round((done / total * 100) if total > 0 else 0),
        "total_tasks":     total,
        "overdue_tasks":   overdue,
    }

@app.get("/projects")
def get_all_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    now = datetime.utcnow()
    result = []
    for p in projects:
        total   = len(p.tasks)
        done    = len([t for t in p.tasks if t.status == "DONE"])
        overdue = len([t for t in p.tasks if t.status != "DONE" and t.deadline and t.deadline < now])
        result.append({
            "id":              p.id,
            "name":            p.name,
            "team_id":         p.team_id,
            "status":          "In Progress" if total > 0 else "Not Started",
            "completion_rate": round((done / total * 100) if total > 0 else 0),
            "total_tasks":     total,
            "overdue_tasks":   overdue,
        })
    return result

# ==========================================
# TASK ROUTES
# ==========================================

@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    user = db.query(User).filter(User.id == task.assigned_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Assigned user not found")
    new_task = Task(
        title=task.title,
        status="TODO",
        project_id=task.project_id,
        assigned_user_id=task.assigned_user_id,
        complexity_score=task.complexity_score,
        deadline=task.deadline
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message": "Task created", "task_id": new_task.id}

@app.put("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status      = "DONE"
    task.completed_at = datetime.utcnow()
    user = db.query(User).filter(User.id == task.assigned_user_id).first()
    if user:
        user.points          = (user.points or 0) + 20
        user.level           = (user.points // 200) + 1
        user.total_completed = (user.total_completed or 0) + 1
    db.commit()
    return {
        "message": "Task completed",
        "points":  user.points if user else 0,
        "level":   user.level  if user else 1
    }

# ✅ FIX: Points are now also awarded when status is set to DONE via the general update endpoint
@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if "status" in updates:
        old_status = task.status
        task.status = updates["status"]

        if updates["status"] == "DONE":
            task.completed_at = datetime.utcnow()
            # ✅ Award points only if task wasn't already DONE
            if old_status != "DONE":
                user = db.query(User).filter(User.id == task.assigned_user_id).first()
                if user:
                    user.points          = (user.points or 0) + 20
                    user.level           = (user.points // 200) + 1
                    user.total_completed = (user.total_completed or 0) + 1
        else:
            task.completed_at = None

    for field in ["title", "deadline", "complexity_score", "assigned_user_id"]:
        if field in updates:
            setattr(task, field, updates[field])

    db.commit()
    db.refresh(task)
    return {"message": "Task updated", "task_id": task.id}

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}

@app.get("/projects/{project_id}/tasks")
def get_project_tasks(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    return [
        {
            "id":               t.id,
            "title":            t.title,
            "status":           t.status,
            "project_id":       t.project_id,
            "assigned_user_id": t.assigned_user_id,
            "complexity_score": t.complexity_score,
            "created_at":       t.created_at.isoformat()   if t.created_at   else None,
            "deadline":         t.deadline.isoformat()      if t.deadline     else None,
            "completed_at":     t.completed_at.isoformat()  if t.completed_at else None,
            "assigned_user": {
                "id":   t.assigned_user.id,
                "name": t.assigned_user.name,
            } if t.assigned_user else None,
        }
        for t in tasks
    ]

# ==========================================
# ANALYTICS
# ==========================================

# ✅ FIX: Overdue now counts non-Done tasks past deadline (consistent with dashboard)
@app.get("/analytics/team/{team_id}")
def get_team_analytics(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    projects    = db.query(Project).filter(Project.team_id == team_id).all()
    project_ids = [p.id for p in projects]
    tasks       = db.query(Task).filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    total       = len(tasks)
    now         = datetime.utcnow()

    if total == 0:
        return {
            "team_completion_rate": 0,
            "team_overdue_rate":    0,
            "team_tpi_score":       0,
            "performance_overview": {"completion": 0, "overdue": 0, "on_track": 0},
            "quick_breakdown": {
                "tasks_completed_on_time": 0,
                "tasks_overdue":           0,
                "team_health_score":       "0 / 100",
                "overall_status":          "No Data"
            }
        }

    completed    = len([t for t in tasks if t.status == "DONE"])
    # ✅ FIX: Consistent overdue definition — non-done tasks past deadline
    overdue      = len([t for t in tasks if t.status != "DONE" and t.deadline and t.deadline < now])
    on_track     = total - overdue - completed
    comp_rate    = completed / total
    overdue_rate = overdue / total
    tpi          = calculate_tpi(comp_rate, 1 - overdue_rate, 0)

    overall_status = "Healthy" if tpi >= 60 else ("At Risk" if tpi >= 40 else "Critical")

    return {
        "team_completion_rate": round(comp_rate * 100, 2),
        "team_overdue_rate":    round(overdue_rate * 100, 2),
        "team_tpi_score":       round(tpi, 1),
        "performance_overview": {
            "completion": round(comp_rate * 100),
            "overdue":    round(overdue_rate * 100),
            "on_track":   round((on_track / total) * 100),
        },
        "quick_breakdown": {
            "tasks_completed_on_time": f"{round(comp_rate * 100)}%",
            "tasks_overdue":           f"{round(overdue_rate * 100)}%",
            "team_health_score":       f"{round(tpi)} / 100",   # ✅ FIX: was "/ 10", now "/ 100"
            "overall_status":          overall_status,
        }
    }

# ==========================================
# DASHBOARD
# ==========================================

@app.get("/dashboard/{team_id}")
def get_dashboard(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    projects    = db.query(Project).filter(Project.team_id == team_id).all()
    project_ids = [p.id for p in projects]
    all_tasks   = db.query(Task).filter(Task.project_id.in_(project_ids)).all() if project_ids else []

    now             = datetime.utcnow()
    total_tasks     = len(all_tasks)
    completed_tasks = len([t for t in all_tasks if t.status == "DONE"])
    in_progress     = len([t for t in all_tasks if t.status == "IN_PROGRESS"])
    todo_tasks      = len([t for t in all_tasks if t.status == "TODO"])
    overdue_tasks   = len([t for t in all_tasks if t.status != "DONE" and t.deadline and t.deadline < now])
    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)

    overdue_rate = overdue_tasks / total_tasks if total_tasks > 0 else 0
    tpi = calculate_tpi(completion_rate / 100, 1 - overdue_rate, 0) if total_tasks > 0 else 0

    if total_tasks == 0:
        risk_level, risk_reason = "No Data", "No tasks yet. Add tasks to generate insights."
    elif tpi >= 80:
        risk_level, risk_reason = "Low Risk", "Team performance is excellent. Keep it up!"
    elif tpi >= 50:
        risk_level, risk_reason = "Moderate Risk", f"{overdue_tasks} tasks overdue. Monitor closely."
    else:
        risk_level, risk_reason = "High Risk", "High overdue rate. Immediate action needed."

    my_tasks     = [t for t in all_tasks if t.assigned_user_id == current_user.id]
    my_completed = len([t for t in my_tasks if t.status == "DONE"])
    my_overdue   = len([t for t in my_tasks if t.status != "DONE" and t.deadline and t.deadline < now])

    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    member_stats = []
    for m in members:
        u           = m.user
        u_tasks     = [t for t in all_tasks if t.assigned_user_id == u.id]
        u_completed = len([t for t in u_tasks if t.status == "DONE"])
        member_stats.append({
            "user_id":         u.id,
            "name":            u.name,
            "points":          getattr(u, "points", 0),
            "level":           getattr(u, "level",  1),
            "streak":          getattr(u, "streak", 0),
            "tasks_completed": u_completed,
            "total_tasks":     len(u_tasks),
        })
    member_stats.sort(key=lambda x: x["points"], reverse=True)

    recent = sorted(
        [t for t in all_tasks if t.status == "DONE"],
        key=lambda t: t.completed_at or t.created_at or now,
        reverse=True
    )[:5]

    recent_tasks = []
    for t in recent:
        assignee = db.query(User).filter(User.id == t.assigned_user_id).first()
        recent_tasks.append({
            "id":       t.id,
            "title":    t.title,
            "status":   t.status,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "assignee": assignee.name if assignee else "Unassigned",
        })

    projects_summary = []
    for p in projects:
        p_tasks   = [t for t in all_tasks if t.project_id == p.id]
        p_done    = len([t for t in p_tasks if t.status == "DONE"])
        p_total   = len(p_tasks)
        p_overdue = len([t for t in p_tasks if t.status != "DONE" and t.deadline and t.deadline < now])
        projects_summary.append({
            "id":              p.id,
            "name":            p.name,
            "total_tasks":     p_total,
            "completed_tasks": p_done,
            "overdue_tasks":   p_overdue,
            "completion_rate": round((p_done / p_total * 100) if p_total > 0 else 0),
        })

    return {
        "team_id":         team_id,
        "total_projects":  len(projects),
        "total_tasks":     total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress":     in_progress,
        "todo_tasks":      todo_tasks,
        "overdue_tasks":   overdue_tasks,
        "completion_rate": completion_rate,
        "tpi_score":       round(tpi, 1),
        "sprint_progress": completion_rate,
        "risk_level":      risk_level,
        "risk_reason":     risk_reason,
        "my_tasks": {
            "total":     len(my_tasks),
            "completed": my_completed,
            "overdue":   my_overdue,
        },
        "members":      member_stats,
        "recent_tasks": recent_tasks,
        "projects":     projects_summary,
        "user": {
            "id":              current_user.id,
            "name":            current_user.name,
            "points":          getattr(current_user, "points",          0),
            "level":           getattr(current_user, "level",           1),
            "streak":          getattr(current_user, "streak",          0),
            "total_completed": getattr(current_user, "total_completed", 0),
        }
    }
# ==========================================
# AI SUMMARY (Groq)
# ==========================================
@app.post("/ai/summary")
def ai_summary(payload: dict, current_user: User = Depends(get_current_user)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
       raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
              "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": payload.get("system", "")},
                    {"role": "user",   "content": payload.get("prompt", "")},
                ],
                "max_tokens": 300,
            },
            timeout=15,
        )
        print("GROQ STATUS:", res.status_code)
        print("GROQ BODY:", res.text[:300])
        data = res.json()
        text = data["choices"][0]["message"]["content"]
        return {"content": [{"text": text}]}
    except Exception as e:
        print("GROQ ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
# ==========================================
# WEBSOCKET CHAT
# ==========================================

@app.websocket("/ws/chat/{team_id}")
async def websocket_chat(
    websocket: WebSocket,
    team_id: int,
    token: str = Query(...)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=1008)
        return

    db   = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=1008)
        db.close()
        return

    await manager.connect(websocket, team_id, user_id, user.name)

    try:
        while True:
            data     = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "message":
                new_msg = Message(
                    team_id=team_id,
                    user_id=user_id,
                    content=data.get("content"),
                    timestamp=datetime.utcnow()
                )
                db.add(new_msg)
                db.commit()
                db.refresh(new_msg)
                await manager.broadcast_to_team(team_id, {
                    "type":       "message",
                    "message_id": new_msg.id,
                    "user_id":    user_id,
                    "username":   user.name,
                    "content":    data.get("content"),
                    "timestamp":  new_msg.timestamp.isoformat()
                })
            elif msg_type == "typing":
                await manager.send_typing_indicator(team_id, user_id, user.name, data.get("is_typing", False))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        db.close()

# ==========================================
# CHAT HISTORY
# ==========================================

@app.get("/teams/{team_id}/messages")
def get_team_messages(
    team_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    messages = db.query(Message).filter(Message.team_id == team_id)\
        .order_by(desc(Message.timestamp)).limit(limit).all()

    return [
        {
            "id":        m.id,
            "user_id":   m.user_id,
            "username":  m.user.name,
            "content":   m.content,
            "timestamp": m.timestamp.isoformat()
        }
        for m in reversed(messages)
    ]
