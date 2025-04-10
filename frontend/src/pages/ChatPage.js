import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatPage.css';
import TableComponent from '../components/TableComponent.js';
import { FaTrash } from 'react-icons/fa'; // Import the trash icon

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isReplying, setIsReplying] = useState(false);
  const [isSliderCollapsed, setIsSliderCollapsed] = useState(false); // State for slider
  const [databaseNames, setDatabaseNames] = useState([]);
  const [chatName, setChatName] = useState('');
  const [chatNames, setChatNames] = useState([]); // Static chat names for now
  const [chatNamesLoaded, setChatNamesLoaded] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {

    async function fetchDbNames() {
      const response = await fetch("http://localhost:8000/database-names", { method: "GET" });
      const names = await response.json();
      setDatabaseNames(names.folders);
    }
    fetchDbNames();

    async function fetchChatNames() {
      const response = await fetch("http://localhost:8000/allChats", { method: "GET" });
      const names = await response.json();
      setChatNames(names.chatNames);
      setChatNamesLoaded(true)
    }
    fetchChatNames();


  }, []);

  useEffect(()=>{
    if(chatNamesLoaded){
      const randomChatName = `Chat_${chatNames.length+1}`;
      setChatName(randomChatName);
      setChatNamesLoaded(false)
    }
  },[chatNamesLoaded,chatNames?.length])


  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevents adding a new line
      handleSend(); // Calls the send function
    }
  };

  const handleSend = async () => {
      if (!input.trim()) return;
      const userMessage = { sender: 'user', type: 'text', content: input };
      setMessages([...messages, userMessage]);
      setInput('');

      setIsReplying(true);
      const dbName = document.getElementById("databaseChoice").value;
      console.log(dbName);
      await fetch("http://localhost:8000/registerDB", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "dbName": String(dbName)
        })
      });
      const queryRes = await fetch("http://localhost:8000/userQuery", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "dbName": String(dbName),
          "userQuery": String(input)
        })
      });

      const resp = await queryRes.json();

      const modelReply = { sender: 'model', type: resp.type, content: resp.queryResp };
      setMessages((prev) => [...prev, modelReply]);
      setIsReplying(false);

      await fetch("http://localhost:8000/appendMessage", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "chatName": String(chatName),
          "messages":[userMessage,modelReply]
        })
      });

  };

  const handleCreateChat = () => {
    window.location.reload(); // refreshes the current page
    
  };

  const handleChatClick = async (name) => {
      const res=await fetch("http://localhost:8000/getMessages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "chatName": String(name),
        })
      });
      const chatMessages=await res.json();
      console.log(chatMessages)
      setMessages(chatMessages.messages) 

    };
    
    const handleDeleteChat = (name) => {
      console.log(`Delete chat: ${name}`);
      // Functionality to delete the chat will go here
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
        {!isSliderCollapsed && (
          <>
            <button className="create-chat-button" onClick={handleCreateChat}>
              Create Chat
            </button>
            <ul className="chat-list">
              {chatNames.map((name, index) => (
                <li key={index} className="chat-item">
                  <span onClick={() => handleChatClick(name)}>{name}</span>
                  <button className="delete-chat-button" onClick={() => handleDeleteChat(name)}>
                    <FaTrash />
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
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
            } else if (msg.type === 'plot') {
              content = <img src={msg.content} alt="Generated Plot" />;
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