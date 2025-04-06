import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatPage.css';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isReplying, setIsReplying] = useState(false);
  const [isSliderCollapsed, setIsSliderCollapsed] = useState(false); // State for slider
  const navigate = useNavigate();

  const handleSend = () => {
    if (!input.trim()) return;
    const userMessage = { sender: 'user', text: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsReplying(true);

    setTimeout(() => {
      const modelReply = { sender: 'model', text: 'This is a static reply from the model.' };
      setMessages((prev) => [...prev, modelReply]);
      setIsReplying(false);
    }, 2000);
  };

  return (
    <div className="chat-page">
      <div className={`slider ${isSliderCollapsed ? 'collapsed' : ''}`}>
        <button
          className="toggle-slider"
          onClick={() => setIsSliderCollapsed(!isSliderCollapsed)}
        >
          {isSliderCollapsed ? '>' : '<'}
        </button>
        {!isSliderCollapsed && <p>Slider Content</p>}
      </div>
      <div className="chat-content">
        <header className="chat-header">
          <h1>QPGenerator</h1>
          <div className="header-controls">
            <select>
              <option value="">Select Database</option>
              <option value="db1">Database 1</option>
              <option value="db2">Database 2</option>
            </select>
            <button onClick={() => navigate('/create-database')}>Create Database</button>
          </div>
        </header>
        <div className="chat-container">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
              <p><strong>{msg.sender === 'user' ? 'You' : 'AI'}:</strong> {msg.text}</p>
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isReplying}
          />
          <button onClick={handleSend} disabled={isReplying}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default ChatPage;
