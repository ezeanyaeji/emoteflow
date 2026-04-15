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

const COLORS = [
  '#ef4444', // Angry (red)
  '#a855f7', // Disgust (purple)
  '#f59e0b', // Fear (amber)
  '#22c55e', // Happy (green)
  '#3b82f6', // Sad (blue)
  '#ec4899', // Surprise (pink)
  '#6b7280', // Neutral (gray)
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchSummary = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get(`/dashboard/summary?hours=${hours}`);
      setSummary(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [hours]);

  const handleExport = async (format) => {
    try {
      const res = await api.get(
        `/dashboard/export?format=${format}&hours=${hours}`,
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `emotion_report.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error-page">{error}</div>;
  if (!summary) return null;

  const pieData = Object.entries(summary.emotion_distribution).map(
    ([emotion, info]) => ({
      name: emotion,
      value: info.count,
    })
  );

  const barData = Object.entries(summary.emotion_distribution).map(
    ([emotion, info]) => ({
      emotion,
      count: info.count,
      confidence: Math.round(info.avg_confidence * 100),
    })
  );

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Class Emotion Dashboard</h1>
        <div className="dashboard-controls">
          <select value={hours} onChange={(e) => setHours(Number(e.target.value))}>
            <option value={1}>Last 1 hour</option>
            <option value={6}>Last 6 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
          </select>
          <button onClick={() => handleExport('csv')}>Export CSV</button>
          <button onClick={() => handleExport('json')}>Export JSON</button>
        </div>
      </div>

      <div className="stats-cards">
        <div className="stat-card">
          <h3>Total Detections</h3>
          <p className="stat-value">{summary.total_emotion_logs}</p>
        </div>
        <div className="stat-card">
          <h3>Active Students</h3>
          <p className="stat-value">{summary.unique_students}</p>
        </div>
        <div className="stat-card">
          <h3>Dominant Emotion</h3>
          <p className="stat-value">
            {pieData.length > 0 ? pieData[0].name : 'N/A'}
          </p>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Emotion Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Detection Count by Emotion</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="emotion" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {summary.students.length > 0 && (
        <div className="students-table-card">
          <h3>Student Activity</h3>
          <table className="students-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Detections</th>
                <th>Recent Emotion</th>
                <th>Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {summary.students.map((s) => (
                <tr
                  key={s.user_id}
                  className="clickable-row"
                  onClick={() => navigate(`/student/${s.user_id}`)}
                >
                  <td>{s.name || s.user_id.slice(-8)}</td>
                  <td>{s.total_logs}</td>
                  <td>{s.dominant_emotion}</td>
                  <td>{new Date(s.last_seen).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
