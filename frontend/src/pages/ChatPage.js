// todo: everything is ready, just call backend and update messages

import React, { useState,useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatPage.css';
import TableComponent from '../components/TableComponent.js'
function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isReplying, setIsReplying] = useState(false);
  const [isSliderCollapsed, setIsSliderCollapsed] = useState(false); // State for slider
  const [databaseNames,setDatabaseNames]=useState([])
  const navigate = useNavigate();

  useEffect(()=>{
    async function fetchDbNames(){
      const response=await fetch("http://localhost:8000/database-names",{method: "GET"});
      const names=await response.json()
      //console.log(names.folders)
      setDatabaseNames(names.folders);
    }
    fetchDbNames();

  },[])
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevents adding a new line
      handleSend(); // Calls the send function
    }
  };
  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = { sender: 'user',type:'text', content: input };
    setMessages([...messages, userMessage]);
    setInput('');

    setIsReplying(true);
    const dbName = document.getElementById("databaseChoice").value;
    console.log(dbName)
    await fetch("http://localhost:8000/registerDB",{
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body:JSON.stringify({
        "dbName":String(dbName)
      })
    });
    const queryRes=await fetch("http://localhost:8000/userQuery",{
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body:JSON.stringify({
        "dbName":String(dbName),
        "userQuery": String(input)
      })
    });

    const resp=await queryRes.json()


    const modelReply = { sender: 'model', type:resp.type,content: resp.queryResp };
    setMessages((prev) => [...prev, modelReply]);
    setIsReplying(false);

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
      <div className={`chat-section ${isSliderCollapsed ? 'expanded' : ''}`}>
        <header className="chat-header">
          <h1>QPGenerator</h1>
          <div className="header-controls">
            <select id="databaseChoice">
              {databaseNames.map((val) => (
                <option key={val} value={val}>
                  {val}
                </option>
              ))}
            </select>
            <button onClick={() => navigate('/create-database')}>Create Database</button>
          </div>
        </header>
        <div className="chat-container">
          {messages.map((msg, index) => {
            let content;
            if (msg.type === 'text') {
              content = <p>{msg.content}</p>;
            } else if (msg.type === 'table') {
              content = <TableComponent data={msg.content} />;
            }
            else if (msg.type === 'plot') {
              content = <img src={msg.content} alt="Generated Plot"/>;
            }

            return (
              <div key={index} className={`chat-message ${msg.sender}`}>
                {content}
              </div>
            );
          })}
        </div>
        <div className="chat-input">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown} // Handles Enter and Shift+Enter
            disabled={isReplying}
            placeholder="Type your message here..."
          />
        </div>
      </div>
    </div>
  );
}

export default ChatPage;
