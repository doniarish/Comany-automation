import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const EmployeeDashboard = () => {
  const [tasks, setTasks] = useState([]);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      setUser(JSON.parse(userStr));
    }
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/tasks/my', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks', err);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-brand">Company Automation</div>
        <div className="navbar-user">
          <span>{user?.username || 'Employee'}</span>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="container">
        <div className="dashboard-header">
          <h2>My Tasks</h2>
          <p>Here are the tasks assigned to you by your manager.</p>
        </div>

        <div className="tasks-grid">
          {tasks.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', gridColumn: '1/-1' }}>You have no tasks assigned yet.</p>
          ) : (
            tasks.map(task => (
              <div className="task-card" key={task.id}>
                <div className="task-header">
                  <div className="task-title">{task.title}</div>
                  <div className={`task-status status-${task.status}`}>
                    {task.status.replace('_', ' ')}
                  </div>
                </div>
                <div className="task-desc">{task.description || 'No description provided.'}</div>
                <div className="task-meta">
                  <span>Task ID: #{task.id}</span>
                  <span>Assigned: {formatDate(task.created_at)}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
};

export default EmployeeDashboard;
