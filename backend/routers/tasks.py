from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from database import execute_query
from auth_utils import get_current_user, require_role

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    title: str
    description: str
    employee_id: int

@router.get("/my")
def get_my_tasks(user = Depends(require_role("employee"))):
    new_query = "SELECT * FROM tasks WHERE employee_id = %s ORDER BY created_at DESC"
    new_tasks = execute_query(new_query, (user["id"],))
    
    legacy_query = "SELECT * FROM task_details WHERE owner = %s"
    legacy_results = execute_query(legacy_query, (user["id"],))
    
    tasks_list = []
    if not isinstance(new_tasks, str):
        tasks_list.extend(new_tasks)
        
    if not isinstance(legacy_results, str):
        import json
        for row in legacy_results:
            if row.get("task_value"):
                try:
                    val_data = row["task_value"]
                    if isinstance(val_data, bytes):
                        val_data = val_data.decode("utf-8")
                    val = json.loads(val_data)
                    title = val.get("Name", "Untitled Task")
                    
                    impact = val.get('impact', [])
                    if isinstance(impact, str): impact = [impact]
                    desc = f"Impact: {', '.join(impact)}. Priority: {val.get('priority', '')}. Progress: {val.get('progress', 0)}%"
                    
                    raw_status = (val.get("status") or "").lower()
                    if "progress" in raw_status: status = "in_progress"
                    elif "complete" in raw_status: status = "completed"
                    else: status = "pending"
                            
                    tasks_list.append({
                        "id": f"legacy_{row.get('ID', '')}",
                        "title": title,
                        "description": desc,
                        "employee_id": user["id"],
                        "status": status,
                        "created_at": row.get("created_time")
                    })
                except Exception as e:
                    pass

    tasks_list.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return tasks_list

@router.get("/manager")
def get_manager_tasks(user = Depends(require_role("manager"))):
    new_query = """
        SELECT t.id, t.title, t.description, t.employee_id, t.status, t.created_at, e.first_name as employee_name
        FROM tasks t
        LEFT JOIN employee_details e ON t.employee_id = e.emp_id
    """
    new_tasks = execute_query(new_query)
    
    legacy_query = "SELECT * FROM task_details"
    legacy_results = execute_query(legacy_query)
    
    emp_map = {}
    employees = execute_query("SELECT emp_id, first_name FROM employee_details")
    if not isinstance(employees, str):
        for e in employees:
            emp_map[e["emp_id"]] = e["first_name"]
            
    tasks_list = []
    if not isinstance(new_tasks, str):
        tasks_list.extend(new_tasks)
        
    if not isinstance(legacy_results, str):
        import json
        for row in legacy_results:
            if row.get("task_value"):
                try:
                    val_data = row["task_value"]
                    if isinstance(val_data, bytes):
                        val_data = val_data.decode("utf-8")
                    val = json.loads(val_data)
                    title = val.get("Name", "Untitled Task")
                    
                    impact = val.get('impact', [])
                    if isinstance(impact, str): impact = [impact]
                    desc = f"Impact: {', '.join(impact)}. Priority: {val.get('priority', '')}. Progress: {val.get('progress', 0)}%"
                    
                    raw_status = (val.get("status") or "").lower()
                    if "progress" in raw_status: status = "in_progress"
                    elif "complete" in raw_status: status = "completed"
                    else: status = "pending"
                        
                    emp_id = row.get("owner")
                    emp_name = emp_map.get(emp_id, f"User {emp_id}")
                            
                    tasks_list.append({
                        "id": f"legacy_{row.get('ID', '')}",
                        "title": title,
                        "description": desc,
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "status": status,
                        "created_at": row.get("created_time")
                    })
                except Exception as e:
                    pass

    tasks_list.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return tasks_list

@router.get("/stats")
def get_stats(user = Depends(require_role("manager"))):
    tasks_list = get_manager_tasks(user)
    stats = {"pending": 0, "in_progress": 0, "completed": 0}
    for t in tasks_list:
        status = t.get("status", "pending")
        if status in stats:
            stats[status] += 1
    return stats

@router.get("/employees")
def get_employees(search: Optional[str] = None, user = Depends(require_role("manager"))):
    if search:
        query = "SELECT emp_id as id, first_name as username FROM employee_details WHERE user_role = 0 AND first_name LIKE %s"
        employees = execute_query(query, (f"%{search}%",))
    else:
        employees = execute_query("SELECT emp_id as id, first_name as username FROM employee_details WHERE user_role = 0")
    if isinstance(employees, str):
        raise HTTPException(status_code=500, detail=employees)
    return employees

@router.post("")
def create_task(req: TaskCreate, user = Depends(require_role("manager"))):
    query = "INSERT INTO tasks (title, description, employee_id, status) VALUES (%s, %s, %s, 'pending')"
    result = execute_query(query, (req.title, req.description, req.employee_id))
    if isinstance(result, str):
        raise HTTPException(status_code=500, detail=result)
    return {"message": "Task assigned successfully", "id": result}
