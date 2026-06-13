import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Chatbot from '../components/Chatbot';

const ManagerDashboard = () => {
  const [stats, setStats] = useState({ pending: 0, in_progress: 0, completed: 0 });
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('all');
  const [employees, setEmployees] = useState([]);
  const [employeeSearch, setEmployeeSearch] = useState('');
  const [user, setUser] = useState(null);
  const [formData, setFormData] = useState({ employee_id: '', title: '', description: '' });
  const [assignMsg, setAssignMsg] = useState('');
  const [isError, setIsError] = useState(false);
  
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) setUser(JSON.parse(userStr));
    
    loadStats();
    loadEmployees();
    loadTasks();
  }, []);

  const loadStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/tasks/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setStats({
        pending: data.pending || 0,
        in_progress: data.in_progress || 0,
        completed: data.completed || 0
      });
    } catch (err) {
      console.error(err);
    }
  };

  const loadEmployees = async (searchStr = '') => {
    try {
      const url = searchStr 
        ? `http://localhost:8000/api/tasks/employees?search=${encodeURIComponent(searchStr)}` 
        : 'http://localhost:8000/api/tasks/employees';
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setEmployees(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      loadEmployees(employeeSearch);
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [employeeSearch]);

  const loadTasks = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/tasks/manager', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setTasks(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAssignTask = async (e) => {
    e.preventDefault();
    setAssignMsg('');
    try {
      const res = await fetch('http://localhost:8000/api/tasks', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to assign task');
      
      setIsError(false);
      setAssignMsg('Task assigned successfully!');
      setFormData({ employee_id: '', title: '', description: '' });
      
      loadStats();
      loadTasks();
      
      setTimeout(() => setAssignMsg(''), 3000);
    } catch (err) {
      setIsError(true);
      setAssignMsg(err.message);
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

  const handleFilterClick = (status) => {
    setFilter(prev => prev === status ? 'all' : status);
  };

  const filteredTasks = tasks.filter(task => filter === 'all' || task.status === filter);

  return (
    <>
      <nav className="navbar">
        <div className="navbar-brand">Company Automation</div>
        <div className="navbar-user">
          <span>{user?.username || 'Manager'}</span>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="container">
        <div className="dashboard-header">
          <h2>Manager Dashboard</h2>
          <p>Overview of your team's tasks and performance.</p>
        </div>

        <div className="stats-grid">
          <div 
            className="stat-card pending"
            onClick={() => handleFilterClick('pending')}
            style={{ cursor: 'pointer', opacity: filter === 'all' || filter === 'pending' ? 1 : 0.5, transition: 'opacity 0.2s' }}
          >
            <div className="stat-title">Pending Tasks</div>
            <div className="stat-value">{stats.pending}</div>
          </div>
          <div 
            className="stat-card progress"
            onClick={() => handleFilterClick('in_progress')}
            style={{ cursor: 'pointer', opacity: filter === 'all' || filter === 'in_progress' ? 1 : 0.5, transition: 'opacity 0.2s' }}
          >
            <div className="stat-title">In Progress</div>
            <div className="stat-value">{stats.in_progress}</div>
          </div>
          <div 
            className="stat-card completed"
            onClick={() => handleFilterClick('completed')}
            style={{ cursor: 'pointer', opacity: filter === 'all' || filter === 'completed' ? 1 : 0.5, transition: 'opacity 0.2s' }}
          >
            <div className="stat-title">Completed</div>
            <div className="stat-value">{stats.completed}</div>
          </div>
        </div>

        <div className="dashboard-grid">
          <div className="form-card">
            <h3>Assign New Task</h3>
            <form onSubmit={handleAssignTask}>
              <div className="form-group">
                <label>Assign To</label>
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder="Search employee..." 
                  style={{ marginBottom: '0.5rem' }}
                  value={employeeSearch}
                  onChange={(e) => setEmployeeSearch(e.target.value)}
                />
                <select 
                  className="form-control" 
                  value={formData.employee_id}
                  onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
                  required
                >
                  <option value="">Select Employee...</option>
                  {employees.map(emp => (
                    <option key={emp.id} value={emp.id}>{emp.username}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Task Title</label>
                <input 
                  type="text" 
                  className="form-control" 
                  required 
                  placeholder="e.g. Update Quarterly Report"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea 
                  className="form-control" 
                  rows="4" 
                  placeholder="Task details..."
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                ></textarea>
              </div>
              {assignMsg && (
                <div className="error-msg" style={{ color: isError ? 'var(--danger)' : 'var(--success)' }}>
                  {assignMsg}
                </div>
              )}
              <button type="submit" className="btn">Assign Task</button>
            </form>
          </div>

          <div>
            <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Team Tasks</h3>
            <div className="tasks-grid" style={{ gridTemplateColumns: '1fr' }}>
              {filteredTasks.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No tasks match the selected filter.</p>
              ) : (
                filteredTasks.map(task => (
                  <div className="task-card" key={task.id}>
                    <div className="task-header">
                      <div>
                        <div className="task-title">{task.title}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                          Assigned to: <span style={{ color: 'white' }}>@{task.employee_name}</span>
                        </div>
                      </div>
                      <div className={`task-status status-${task.status}`}>
                        {task.status.replace('_', ' ')}
                      </div>
                    </div>
                    <div className="task-desc">{task.description || 'No description provided.'}</div>
                    <div className="task-meta">
                      <span>Task ID: #{task.id}</span>
                      <span>Created: {formatDate(task.created_at)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
        <Chatbot />
      </div>
    </>
  );
};

export default ManagerDashboard;
