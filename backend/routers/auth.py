from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import execute_query
from auth_utils import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str = ""

@router.post("/login")
def login(req: LoginRequest):
    users = execute_query("SELECT * FROM employee_details WHERE first_name = %s ORDER BY emp_id DESC LIMIT 1", (req.username,))
    
    if isinstance(users, str) or not users:
        raise HTTPException(status_code=401, detail="Invalid username")
    
    user = users[0]
    
    role = "manager" if user.get("user_role") == 1 else "employee"
    username = user.get("first_name", "Unknown")
    
    token = create_access_token({"id": user["emp_id"], "username": username, "role": role})
    
    return {
        "accessToken": token,
        "id": user["emp_id"],
        "username": username,
        "role": role
    }
