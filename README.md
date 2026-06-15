# Company Automation

Company Automation is a full-stack application designed to streamline internal company operations. It features role-based access control for managers and employees, task management, and an AI-powered chatbot assistant.

## Features

- **Role-Based Access Control**: Different access levels for `manager` and `employee` roles. Managers can assign tasks to their employees.
- **Task Management**: Create, assign, and track the status of tasks (`pending`, `in_progress`, `completed`).
- **AI Chatbot**: Integrated conversational AI agent built with LangChain and LangGraph to assist users.
- **Secure Authentication**: JWT-based authentication and Bcrypt password hashing.

## Tech Stack

- **Frontend**: React, Vite
- **Backend**: Python, FastAPI, Uvicorn
- **AI/LLM**: LangChain, LangGraph, Langchain-Together
- **Database**: MySQL
- **Authentication**: PyJWT, Bcrypt

## Project Structure

- `/backend`: Python FastAPI application providing REST APIs for authentication, tasks, and the chatbot.
- `/frontend`: React frontend application (built with Vite).
- `/database`: SQL scripts for setting up the MySQL database schema.

## Setup Instructions

### 1. Database Setup
1. Ensure you have MySQL installed and running.
2. Run the SQL script located in `/database/schema.sql` to create the `company_automation` database and required tables.

```bash
mysql -u root -p < database/schema.sql
```

### 2. Backend Setup
1. Navigate to the `backend` directory.
2. (Optional) Create and activate a virtual environment.
3. Install the Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

4. Create a `.env` file in the `backend` directory with your database credentials, JWT secret, and API keys (e.g., Together AI key).
5. Start the FastAPI server:

```bash
python main.py
```
*The backend server runs on `http://localhost:3000` by default.*

### 3. Frontend Setup
1. Navigate to the `frontend` directory.
2. Install the Node.js dependencies:

```bash
cd frontend
npm install
```

3. Start the Vite development server:

```bash
npm run dev
```
