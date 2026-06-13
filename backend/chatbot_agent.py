import os
import json
import operator
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_together import ChatTogether
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import execute_query

# 1. Define Tools
@tool
def run_sql_query(query: str) -> str:
    """Executes a raw SQL query on the MySQL database and returns the JSON result."""
    try:
        # For security in a real app, restrict to SELECT, but here we trust the LLM
        res = execute_query(query)
        if isinstance(res, str): # Error returned as string
            return res
        return json.dumps(res, default=str)
    except Exception as e:
        return f"Error executing SQL: {str(e)}"

@tool
def assign_task(employee_id: int, title: str, description: str = "No description provided") -> str:
    """Assigns a new task to an employee. REQUIRES a valid employee_id!"""
    try:
        query = "INSERT INTO tasks (title, description, employee_id, status) VALUES (%s, %s, %s, 'pending')"
        result = execute_query(query, (title, description, employee_id))
        if isinstance(result, str):
            return f"Error assigning task: {result}"
        return f"Task '{title}' assigned successfully to employee ID {employee_id}!"
    except Exception as e:
        return f"Exception: {str(e)}"

@tool
def get_employee_tasks(employee_id: int) -> str:
    """Gets all tasks (both new and legacy) for a specific employee."""
    try:
        new_tasks = execute_query("SELECT title, description, status FROM tasks WHERE employee_id = %s", (employee_id,))
        legacy = execute_query("SELECT task_value FROM task_details WHERE owner = %s", (employee_id,))
        
        all_tasks = []
        if not isinstance(new_tasks, str):
            all_tasks.extend(new_tasks)
            
        if not isinstance(legacy, str):
            import json
            for row in legacy:
                if row.get("task_value"):
                    try:
                        val_data = row["task_value"]
                        if isinstance(val_data, bytes):
                            val_data = val_data.decode("utf-8")
                        val = json.loads(val_data)
                        
                        raw_status = (val.get("status") or "").lower()
                        if "progress" in raw_status: status = "in_progress"
                        elif "complete" in raw_status: status = "completed"
                        else: status = "pending"
                        
                        all_tasks.append({
                            "title": val.get("Name", "Untitled"),
                            "description": "Legacy Task",
                            "status": status
                        })
                    except: pass
        
        if not all_tasks: return "This employee has no tasks."
        return json.dumps(all_tasks, indent=2)
    except Exception as e:
        return f"Error fetching tasks: {str(e)}"

tools = [run_sql_query, assign_task, get_employee_tasks]

# 2. State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    iterations: int
    user_query: str

# 3. Initialize LLM
llm = ChatTogether(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo", 
    temperature=0.0, 
    together_api_key=os.getenv("TOGETHER_API_KEY")
)
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a helpful AI assistant for a Manager Dashboard.
You have access to a MySQL database with the following schema:

TABLE employee_details (
  emp_id INT PRIMARY KEY,
  first_name VARCHAR,
  last_name VARCHAR,
  user_role INT
);

TABLE task_details (
  ID INT PRIMARY KEY,
  owner INT,
  task_value JSON,
  created_time DATETIME
);

TABLE tasks (
  id INT PRIMARY KEY,
  title VARCHAR,
  description TEXT,
  employee_id INT,
  status ENUM('pending', 'in_progress', 'completed'),
  created_at TIMESTAMP
);

CRITICAL RULES:
1. DO NOT GUESS OR INVENT DATA. NEVER guess an `employee_id`.
2. To assign a task, you MUST STRICTLY follow a 2-step process:
   - Step 1: Call `run_sql_query` to search for the employee's ID using a fuzzy search (e.g. `SELECT emp_id, first_name FROM employee_details WHERE first_name LIKE '%Ajay%'`).
   - Step 2: Only after receiving the SQL result containing the correct `emp_id`, call `assign_task` using that exact ID.
3. To answer questions about an employee's tasks, ALWAYS use the `get_employee_tasks` tool instead of writing complex SQL queries.
4. DO NOT write SQL queries or python code inside your text response. You MUST use the provided tools (`run_sql_query`, `assign_task`, `get_employee_tasks`) by emitting a valid tool call.
5. TASK TITLE AND DESCRIPTION: When assigning a task, use the user's EXACT words as the task title. Do NOT paraphrase, summarize, or invent a title. For example, if the user says "do the work fast", the title must be "do the work fast". Use the same text as the description if no separate description is provided.
"""



def agent_node(state: AgentState):
    msgs = list(state["messages"])
    if not msgs or not isinstance(msgs[0], BaseMessage) or msgs[0].content != SYSTEM_PROMPT:
        msgs.insert(0, HumanMessage(content=SYSTEM_PROMPT))
        
    response = llm_with_tools.invoke(msgs)
    return {"messages": [response]}

def tool_node(state: AgentState):
    last_msg = state["messages"][-1]
    tool_outputs = []
    
    for tool_call in last_msg.tool_calls:
        action = next((t for t in tools if t.name == tool_call["name"]), None)
        if not action:
            tool_outputs.append(ToolMessage(content=f"Tool {tool_call['name']} not found.", tool_call_id=tool_call["id"]))
            continue
            
        try:
            result = action.invoke(tool_call["args"])
        except Exception as e:
            result = f"Error: {e}"
        tool_outputs.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
        
    return {"messages": tool_outputs}

class NeedsRetry(BaseModel):
    needs_retry: bool = Field(description="True if the tool execution failed, returned an error, or returned an empty result when data was expected.")

def review_node(state: AgentState):
    last_msg = state["messages"][-1]
    user_query = state["user_query"]
    iters = state.get("iterations", 0)
    
    prompt = f"""User query: {user_query}
Tool Output: {last_msg.content}
Review the tool output. You must answer `true` (needs retry) ONLY if:
1. There is an SQL error (e.g. "Error executing SQL: ...").

You must answer `false` (no retry needed) if:
1. The tool executed successfully and returned data (like an ID or success message).
2. The output is empty `[]`. An empty result is a valid factual answer (e.g. there are 0 tasks). NEVER flag an empty array as a failure.

Respond with JSON formatting."""
    
    try:
        evaluator_llm = llm.with_structured_output(NeedsRetry)
        eval_res = evaluator_llm.invoke([HumanMessage(content=prompt)])
        needs_retry = eval_res.needs_retry
    except Exception as e:
        needs_retry = False 
        
    if needs_retry:
        iters += 1
        if iters >= 3:
            return {
                "messages": [AIMessage(content="I'm sorry, I could not find the required information in the database after 3 attempts.")],
                "iterations": iters
            }
        return {
            "messages": [HumanMessage(content="The tool execution failed or returned no data. Please adjust your query and try again.")],
            "iterations": iters
        }
    
    # Reset iterations on success so it can continue with other tools
    return {"iterations": 0}

def route_after_agent(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "end"

def route_after_tools(state: AgentState):
    # Proceed to review node
    return "review"

def route_after_review(state: AgentState):
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and "after 3 attempts" in last_msg.content:
        return "end"
    # Go back to agent to either generate final response (if resolved) or try new tool call (if not resolved)
    return "agent"

# Build Graph
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("review", review_node)

graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "end": END})
graph_builder.add_edge("tools", "review")
graph_builder.add_conditional_edges("review", route_after_review, {"agent": "agent", "end": END})

chat_graph = graph_builder.compile()

async def invoke_chatbot(user_input: str):
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "iterations": 0,
        "user_query": user_input
    }
    # Invoke graph asynchronously
    final_state = await chat_graph.ainvoke(initial_state)
    return final_state["messages"][-1].content
