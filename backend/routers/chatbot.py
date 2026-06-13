from fastapi import APIRouter, Depends
from pydantic import BaseModel
from auth_utils import require_role
from chatbot_agent import invoke_chatbot

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

class ChatRequest(BaseModel):
    message: str

@router.post("")
async def chat_with_agent(req: ChatRequest, user = Depends(require_role("manager"))):
    try:
        response = await invoke_chatbot(req.message)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error interacting with AI: {str(e)}"}
