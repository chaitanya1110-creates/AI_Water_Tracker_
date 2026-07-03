import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Droplet, Send, User, Activity, MessageSquare, Plus } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [userName, setUserName] = useState(localStorage.getItem('water_tracker_user') || '');
  const [isNameSet, setIsNameSet] = useState(!!userName);
  const [intakeAmount, setIntakeAmount] = useState(250);
  const [summary, setSummary] = useState({ total_intake_ml: 0, goal_ml: 2500, remaining_ml: 2500, entries: [] });
  const [insight, setInsight] = useState('');
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isNameSet) {
      fetchSummary();
      fetchInsight();
      localStorage.setItem('water_tracker_user', userName);
    }
  }, [isNameSet]);

  useEffect(scrollToBottom, [chatHistory]);

  const fetchSummary = async () => {
    try {
      const res = await axios.get(`${API_BASE}/intake?user_name=${userName}`);
      setSummary(res.data);
    } catch (err) {
      console.error("Error fetching summary:", err);
    }
  };

  const fetchInsight = async () => {
    try {
      const res = await axios.get(`${API_BASE}/insight?user_name=${userName}`);
      setInsight(res.data.ai_summary);
    } catch (err) {
      console.error("Error fetching insight:", err);
    }
  };

  const handleLogIntake = async () => {
    if (!intakeAmount || intakeAmount <= 0) return;
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/intake`, {
        user_name: userName,
        water_intake_ml: parseInt(intakeAmount)
      });
      await fetchSummary();
      await fetchInsight();
      setIntakeAmount(250);
    } catch (err) {
      console.error("Error logging intake:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!chatMessage.trim()) return;
    const userMsg = chatMessage;
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);
    
    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        user_name: userName,
        message: userMsg
      });
      setChatHistory(prev => [...prev, { role: 'ai', content: res.data.answer }]);
      // Refresh stats in case AI chat mentioned something or we want updated info
      fetchSummary();
    } catch (err) {
      console.error("Error sending message:", err);
      setChatHistory(prev => [...prev, { role: 'ai', content: "Sorry, I'm having trouble connecting right now." }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (userName.trim()) {
      setIsNameSet(true);
    }
  };

  const progressPercentage = Math.min((summary.total_intake_ml / summary.goal_ml) * 100, 100);

  if (!isNameSet) {
    return (
      <div className="card" style={{ marginTop: '10vh' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Droplet size={48} color="#0077be" style={{ marginBottom: '1rem' }} />
          <h1>Water Tracker</h1>
          <p>Stay hydrated with AI-powered insights</p>
        </div>
        <form onSubmit={handleNameSubmit}>
          <div style={{ position: 'relative' }}>
            <User size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
            <input 
              type="text" 
              placeholder="Enter your name to start" 
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              style={{ paddingLeft: '40px' }}
              required
            />
          </div>
          <button type="submit" className="btn" style={{ width: '100%', padding: '0.8rem' }}>
            Get Started
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="container">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Droplet size={24} color="#0077be" />
          <h2 style={{ margin: 0 }}>Hello, {userName}</h2>
        </div>
        <button className="btn btn-secondary" onClick={() => {
          setIsNameSet(false);
          setUserName('');
          localStorage.removeItem('water_tracker_user');
        }} style={{ padding: '0.3rem 0.6rem', fontSize: '0.7rem' }}>
          Change User
        </button>
      </header>

      <section className="card">
        <div className="grid">
          <div className="stat-card">
            <div className="stat-value">{summary.total_intake_ml} ml</div>
            <div className="stat-label">Drunk Today</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.goal_ml} ml</div>
            <div className="stat-label">Daily Goal</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{Math.max(0, summary.remaining_ml)} ml</div>
            <div className="stat-label">Remaining</div>
          </div>
        </div>
        
        <div className="progress-container">
          <div className="progress-bar" style={{ width: `${progressPercentage}%` }}></div>
        </div>
        <div style={{ textAlign: 'right', fontSize: '0.8rem', color: '#64748b' }}>
          {Math.round(progressPercentage)}% of daily goal
        </div>
      </section>

      <section className="card">
        <h3><Plus size={18} style={{ verticalAlign: 'text-bottom', marginRight: '4px' }} /> Log Intake</h3>
        <div className="flex">
          <input 
            type="number" 
            value={intakeAmount} 
            onChange={(e) => setIntakeAmount(e.target.value)}
            placeholder="Amount in ml"
            style={{ marginBottom: 0 }}
          />
          <button className="btn" onClick={handleLogIntake} disabled={loading}>
            {loading ? 'Logging...' : 'Log Water'}
          </button>
        </div>
        <div className="grid" style={{ marginTop: '1rem', gridTemplateColumns: 'repeat(4, 1fr)' }}>
          {[100, 250, 500, 750].map(amount => (
            <button 
              key={amount} 
              className="btn btn-secondary" 
              style={{ padding: '0.4rem', fontSize: '0.8rem' }}
              onClick={() => setIntakeAmount(amount)}
            >
              +{amount}ml
            </button>
          ))}
        </div>
      </section>

      {insight && (
        <section className="card" style={{ borderLeft: '4px solid var(--secondary-turquoise)' }}>
          <h3><Activity size={18} style={{ verticalAlign: 'text-bottom', marginRight: '4px' }} /> AI Insight</h3>
          <p style={{ fontSize: '0.95rem', fontStyle: 'italic', margin: 0 }}>"{insight}"</p>
        </section>
      )}

      <section className="card">
        <h3><MessageSquare size={18} style={{ verticalAlign: 'text-bottom', marginRight: '4px' }} /> AI Coach</h3>
        <div className="chat-box">
          {chatHistory.length === 0 && (
            <p style={{ textAlign: 'center', color: '#64748b', marginTop: '4rem' }}>
              Ask me anything about your hydration!
            </p>
          )}
          {chatHistory.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          {chatLoading && <div className="message ai">Thinking...</div>}
          <div ref={chatEndRef} />
        </div>
        <div className="flex">
          <input 
            type="text" 
            value={chatMessage} 
            onChange={(e) => setChatMessage(e.target.value)}
            placeholder="Type a message..."
            style={{ marginBottom: 0 }}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <button className="btn" onClick={handleSendMessage} disabled={chatLoading}>
            <Send size={18} />
          </button>
        </div>
      </section>
    </div>
  );
}

export default App;
