import { useState, useEffect } from 'react';
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
  LineChart,
  Line,
} from 'recharts';
import api from '../api/axios';
import Spinner from '../components/Spinner';

const EMOTION_COLORS = {
  Angry: '#ef4444',
  Disgust: '#a855f7',
  Fear: '#f59e0b',
  Happy: '#22c55e',
  Neutral: '#6b7280',
  Sad: '#3b82f6',
  Surprise: '#ec4899',
};

const EMOTION_EMOJI = {
  Happy: '😊',
  Sad: '😢',
  Angry: '😠',
  Fear: '😨',
  Surprise: '😲',
  Disgust: '🤢',
  Neutral: '😐',
};

export default function MyHistory() {
  const [data, setData] = useState(null);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchSummary = async () => {
    setLoading(true);
    setError('');
    try {
      const { data: d } = await api.get(`/emotion/my-summary?hours=${hours}`);
      setData(d);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load your emotion history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [hours]);

  if (loading) return <Spinner />;
  if (error) return <div className="error-page">{error}</div>;
  if (!data) return null;

  const { emotion_distribution, timeline, recent_emotions } = data;

  const pieData = Object.entries(emotion_distribution).map(([emotion, info]) => ({
    name: emotion,
    value: info.count,
  }));

  const barData = Object.entries(emotion_distribution).map(([emotion, info]) => ({
    emotion,
    count: info.count,
    confidence: Math.round(info.avg_confidence * 100),
  }));

  const timelineData = Object.entries(timeline).map(([hour, emotions]) => ({
    hour: new Date(hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    ...emotions,
  }));
  const allEmotions = [...new Set(Object.values(timeline).flatMap(Object.keys))];

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h1>My Emotion History</h1>
          <p className="student-email">Your personal emotion analytics</p>
        </div>
        <div className="dashboard-controls">
          <select value={hours} onChange={(e) => setHours(Number(e.target.value))}>
            <option value={1}>Last 1 hour</option>
            <option value={6}>Last 6 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-cards">
        <div className="stat-card">
          <h3>Total Detections</h3>
          <p className="stat-value">{data.total_logs}</p>
        </div>
        <div className="stat-card">
          <h3>Dominant Emotion</h3>
          <p className="stat-value">
            {EMOTION_EMOJI[data.dominant_emotion] || ''} {data.dominant_emotion}
          </p>
        </div>
        <div className="stat-card">
          <h3>Period</h3>
          <p className="stat-value">{hours >= 24 ? `${hours / 24}d` : `${hours}h`}</p>
        </div>
      </div>

      {/* Charts */}
      {pieData.length > 0 ? (
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
                  {pieData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={EMOTION_COLORS[entry.name] || '#6b7280'}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Detection Count</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="emotion" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {barData.map((entry) => (
                    <Cell
                      key={entry.emotion}
                      fill={EMOTION_COLORS[entry.emotion] || '#6b7280'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="chart-card" style={{ textAlign: 'center', padding: '2rem' }}>
          <p>No emotion data recorded yet. Start an Emotion Capture session to see your analytics!</p>
        </div>
      )}

      {/* Timeline */}
      {timelineData.length > 0 && (
        <div className="chart-card" style={{ marginBottom: '1.5rem' }}>
          <h3>Emotion Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              {allEmotions.map((emo) => (
                <Line
                  key={emo}
                  type="monotone"
                  dataKey={emo}
                  stroke={EMOTION_COLORS[emo] || '#6b7280'}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent detections */}
      {recent_emotions.length > 0 && (
        <div className="admin-section">
          <h3>Recent Detections</h3>
          <table className="students-table">
            <thead>
              <tr>
                <th>Emotion</th>
                <th>Confidence</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {recent_emotions.map((r, i) => (
                <tr key={i}>
                  <td>
                    {EMOTION_EMOJI[r.emotion] || ''} {r.emotion}
                  </td>
                  <td>{(r.confidence * 100).toFixed(1)}%</td>
                  <td>{new Date(r.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
