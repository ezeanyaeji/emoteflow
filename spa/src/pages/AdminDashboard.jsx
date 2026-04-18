import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import api from '../api/axios';
import Spinner from '../components/Spinner';

const ROLE_COLORS = { student: '#3b82f6', teacher: '#22c55e', admin: '#f59e0b' };
const EMOTION_COLORS = [
  '#ef4444', '#a855f7', '#f59e0b', '#22c55e', '#3b82f6', '#ec4899', '#6b7280',
];

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [userTotal, setUserTotal] = useState(0);
  const [roleFilter, setRoleFilter] = useState('');
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Create teacher form
  const [showForm, setShowForm] = useState(false);
  const [teacherForm, setTeacherForm] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');

  // Teacher-student assignment state
  const [teachers, setTeachers] = useState([]);
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [assignedIds, setAssignedIds] = useState([]);
  const [allStudents, setAllStudents] = useState([]);
  const [assignSearch, setAssignSearch] = useState('');
  const [assignMsg, setAssignMsg] = useState('');

  const fetchStats = async () => {
    try {
      const { data } = await api.get(`/admin/stats?hours=${hours}`);
      setStats(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load stats');
    }
  };

  const fetchUsers = async () => {
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (roleFilter) params.set('role', roleFilter);
      const { data } = await api.get(`/admin/users?${params}`);
      setUsers(data.users);
      setUserTotal(data.total);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load users');
    }
  };

  const fetchTeachers = async () => {
    try {
      const { data } = await api.get('/admin/users?role=teacher&limit=100');
      setTeachers(data.users || []);
    } catch {
      /* non-critical */
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchStats(), fetchUsers(), fetchTeachers()]).finally(() =>
      setLoading(false)
    );
  }, [hours, roleFilter]);

  // Load assigned students when a teacher is selected
  useEffect(() => {
    if (!selectedTeacherId) return;
    api
      .get(`/admin/assignments/${selectedTeacherId}`)
      .then(({ data }) => setAssignedIds(data.student_ids || []))
      .catch(() => setAssignedIds([]));
  }, [selectedTeacherId]);

  // Load available students for assignment search
  useEffect(() => {
    api
      .get(`/assignments/available-students?search=${assignSearch}`)
      .then(({ data }) => setAllStudents(data.students || []))
      .catch(() => setAllStudents([]));
  }, [assignSearch]);

  const toggleAssignStudent = (id) => {
    setAssignedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const saveAdminAssignments = async () => {
    if (!selectedTeacherId) return;
    setAssignMsg('');
    try {
      await api.put(`/admin/assignments/${selectedTeacherId}`, {
        student_ids: assignedIds,
      });
      setAssignMsg('Assignments saved successfully!');
    } catch (err) {
      setAssignMsg(err.response?.data?.detail || 'Failed to save assignments');
    }
  };

  const handleCreateTeacher = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormSuccess('');
    try {
      const { data } = await api.post('/admin/teachers', teacherForm);
      setFormSuccess(`Teacher ${data.first_name} ${data.last_name} created successfully`);
      setTeacherForm({ email: '', password: '', first_name: '', last_name: '' });
      fetchUsers();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create teacher');
    }
  };

  const handleDeleteUser = async (userId, name) => {
    if (!window.confirm(`Delete user "${name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      fetchUsers();
      fetchStats();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  const updateField = (field) => (e) =>
    setTeacherForm((prev) => ({ ...prev, [field]: e.target.value }));

  if (loading) return <Spinner />;
  if (error && !stats) return <div className="error-page">{error}</div>;

  const roleData = stats
    ? Object.entries(stats.user_counts).map(([role, count]) => ({ role, count }))
    : [];

  const emotionPieData = stats
    ? Object.entries(stats.emotion_distribution).map(([emotion, info]) => ({
        name: emotion,
        value: info.count,
      }))
    : [];

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="dashboard-controls">
          <select value={hours} onChange={(e) => setHours(Number(e.target.value))}>
            <option value={1}>Last 1 hour</option>
            <option value={6}>Last 6 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
          </select>
        </div>
      </div>

      {/* Stats cards */}
      <div className="stats-cards">
        <div className="stat-card">
          <h3>Total Users</h3>
          <p className="stat-value">{stats?.total_users || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Students</h3>
          <p className="stat-value">{stats?.user_counts?.student || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Teachers</h3>
          <p className="stat-value">{stats?.user_counts?.teacher || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Active Students</h3>
          <p className="stat-value">{stats?.active_students || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Emotion Logs</h3>
          <p className="stat-value">{stats?.total_emotion_logs || 0}</p>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3>Users by Role</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={roleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="role" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {roleData.map((entry) => (
                  <Cell key={entry.role} fill={ROLE_COLORS[entry.role] || '#6b7280'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Emotion Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={emotionPieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
              >
                {emotionPieData.map((_, i) => (
                  <Cell key={i} fill={EMOTION_COLORS[i % EMOTION_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Create Teacher */}
      <div className="admin-section">
        <div className="section-header">
          <h3>Teacher Management</h3>
          <button
            className="btn-secondary"
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? 'Cancel' : '+ Create Teacher'}
          </button>
        </div>

        {showForm && (
          <form className="create-teacher-form" onSubmit={handleCreateTeacher}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="t_first">First Name</label>
                <input
                  id="t_first"
                  type="text"
                  value={teacherForm.first_name}
                  onChange={updateField('first_name')}
                  required
                  placeholder="Jane"
                />
              </div>
              <div className="form-group">
                <label htmlFor="t_last">Last Name</label>
                <input
                  id="t_last"
                  type="text"
                  value={teacherForm.last_name}
                  onChange={updateField('last_name')}
                  required
                  placeholder="Smith"
                />
              </div>
              <div className="form-group">
                <label htmlFor="t_email">Email</label>
                <input
                  id="t_email"
                  type="email"
                  value={teacherForm.email}
                  onChange={updateField('email')}
                  required
                  placeholder="teacher@school.edu"
                />
              </div>
              <div className="form-group">
                <label htmlFor="t_pass">Password</label>
                <input
                  id="t_pass"
                  type="password"
                  value={teacherForm.password}
                  onChange={updateField('password')}
                  required
                  minLength={8}
                  placeholder="Min 8 characters"
                />
              </div>
            </div>
            {formError && <p className="error">{formError}</p>}
            {formSuccess && <p className="success">{formSuccess}</p>}
            <button type="submit" className="btn-create">Create Teacher Account</button>
          </form>
        )}
      </div>

      {/* User list */}
      <div className="admin-section">
        <div className="section-header">
          <h3>All Users ({userTotal})</h3>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">All roles</option>
            <option value="student">Students</option>
            <option value="teacher">Teachers</option>
            <option value="admin">Admins</option>
          </select>
        </div>
        <table className="students-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr
                key={u.id}
                className={u.role === 'student' ? 'clickable-row' : ''}
                onClick={() => u.role === 'student' && navigate(`/student/${u.id}`)}
              >
                <td>{u.first_name} {u.last_name}</td>
                <td>{u.email}</td>
                <td>
                  <span className={`role-badge role-${u.role}`}>{u.role}</span>
                </td>
                <td>{new Date(u.created_at).toLocaleDateString()}</td>
                <td>
                  {u.role !== 'admin' && (
                    <button
                      className="btn-delete"
                      onClick={() =>
                        handleDeleteUser(u.id, `${u.first_name} ${u.last_name}`)
                      }
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent users */}
      {stats?.recent_users?.length > 0 && (
        <div className="admin-section">
          <h3>Recent Registrations</h3>
          <table className="students-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Registered</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_users.map((u) => (
                <tr key={u.id}>
                  <td>{u.first_name} {u.last_name}</td>
                  <td>{u.email}</td>
                  <td>
                    <span className={`role-badge role-${u.role}`}>{u.role}</span>
                  </td>
                  <td>{new Date(u.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Assign Students to Teacher */}
      <div className="admin-section">
        <h3>Assign Students to Teacher</h3>
        <div className="form-group" style={{ maxWidth: 360 }}>
          <label>Select Teacher</label>
          <select
            value={selectedTeacherId}
            onChange={(e) => {
              setSelectedTeacherId(e.target.value);
              setAssignMsg('');
            }}
          >
            <option value="">-- Choose a teacher --</option>
            {teachers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.first_name} {t.last_name} ({t.email})
                </option>
              ))}
          </select>
        </div>

        {selectedTeacherId && (
          <div className="assign-panel">
            <div className="form-group">
              <input
                type="text"
                placeholder="Search students by name or email..."
                value={assignSearch}
                onChange={(e) => setAssignSearch(e.target.value)}
              />
            </div>
            {allStudents.length === 0 ? (
              <p className="assign-empty">No students found.</p>
            ) : (
              <div className="assign-list">
                {allStudents.map((s) => (
                  <label key={s.id} className="assign-item">
                    <input
                      type="checkbox"
                      checked={assignedIds.includes(s.id)}
                      onChange={() => toggleAssignStudent(s.id)}
                    />
                    <span>
                      {s.first_name} {s.last_name}
                    </span>
                    <span className="assign-email">{s.email}</span>
                  </label>
                ))}
              </div>
            )}
            {assignMsg && (
              <p className={assignMsg.includes('success') ? 'success' : 'error'}>
                {assignMsg}
              </p>
            )}
            <button className="btn-create" onClick={saveAdminAssignments}>
              Save Assignments ({assignedIds.length} students)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
