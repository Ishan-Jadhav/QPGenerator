// todo: make sure that user only gives query when chatName is properly set
// when chat name is set, highlight the chat in slider

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
  const [loading,setLoading]= useState(false)
  const [databaseNames, setDatabaseNames] = useState([]);
  const [chatName, setChatName] = useState('Chat');
  const [chatNames, setChatNames] = useState([]); // Static chat names for now
  const [totalChats,setTotalChats]=useState(0);
  const [user,setUser]=useState('')
  const navigate = useNavigate();

  useEffect(() => {
        async function auth() {
        
          const res = await fetch("http://localhost:8000/auth-status", {
            method: "POST",
            credentials: "include",
          });
          if (!res.ok) navigate("/signin");
          const data = await res.json();
          setUser(data.user);
      }
      auth();
  }, [navigate]);

  useEffect(() => {
    if(!user) return;
    async function fetchDbNames() {
      const response = await fetch("http://localhost:8000/database-names", { method: "GET" ,credentials:"include"});
      const names = await response.json();

      console.log()
      if(names.folders.length===0)
      {
        navigate('/create-database');
      }

      setDatabaseNames(names.folders);
    }
    fetchDbNames();

    async function fetchChatNames() {
      const response = await fetch("http://localhost:8000/allChats", { method: "GET",credentials:"include" });
      const names = await response.json();
      setChatNames(names.chatNames);
      setTotalChats(names.chatNames.length)
    }
    fetchChatNames();


  }, [navigate,user]);

  useEffect(() => {
    if(!user) return;
    if (chatName !== 'Chat') {
      setLoading(false); // Stop loading when chatName is set
    }
  }, [chatName,user]);


  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevents adding a new line
      handleSend(); // Calls the send function
    }
  };

  const handleSend = async () => {
      if (!input.trim()) return;
      const userMessage = { sender: 'user', type: 'text', content: input };
      setMessages((prev)=>[...prev, userMessage]);
      setInput('');

      setIsReplying(true);
      const dbName = document.getElementById("databaseChoice").value;
      console.log(dbName);
      await fetch("http://localhost:8000/registerDB", {
        method: "POST",
        credentials:"include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "dbName": String(dbName)
        })
      });

      let Cname=chatName;
      if(chatName==="Chat")
      {
          const msg=userMessage.content;
          const rawWords = msg.split(/\s+/).slice(0, 4);
          const cleanWords = rawWords.map(word => word.replace(/[.,/#!$%^&*;:{}=\-_`~()]/g, ''));
          const safeString = cleanWords.join("_")+"_"+totalChats;
          setTotalChats(prev => prev + 1);
          Cname=safeString;
          setLoading(true);
          setChatName(safeString);
          setChatNames((prev) => [...prev,safeString]);
          
      }

      const queryRes = await fetch("http://localhost:8000/userQuery", {
        method: "POST",
        credentials:"include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "dbName": String(dbName),
          "userQuery": String(input),
          "chatName":String(Cname)
        })
      });

      const resp = await queryRes.json();

      const modelReply = { sender: 'model', type: resp.type, content: resp.queryResp };
      setMessages((prev) =>[...prev, modelReply]);
      setIsReplying(false);

  };

  const handleCreateChat = () => {
    window.location.reload(); // refreshes the current page
    
  };

  const handleChatClick = async (name) => {
      if(name===chatName)
        return;
      setLoading(true);
      const res=await fetch("http://localhost:8000/getMessages", {
        method: "POST",
        credentials:"include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "chatName": String(name),
        })
      });
      const chatMessages=await res.json();
      
      setChatName(name);
      setMessages(chatMessages.messages); 
      // setLoading(false);
    };
    
  const handleDeleteChat = async (name) => {
        setChatNames(prevItems => prevItems.filter(item => item !== name));
        await fetch("http://localhost:8000/deleteChat", {
          method: "POST",
          credentials:"include",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            "chatName": String(name),
          })
        });

        if(name === chatName)
          {
            window.location.reload();
          }
        
    };
  const chatNameUI=(name)=>{
    const final=name.split("_").slice(0, -1).join("_");
    return final;
  }
  
  const signout=async ()=>{
      await fetch("http://localhost:8000/signout",{method:"POST",credentials:"include"})
      navigate("/signin")
  }

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
                <li
                  key={index}
                  className={`chat-item ${name === chatName ? 'active-chat' : ''}`} // Add 'active-chat' class if the chat is active
                >
                  <span onClick={() => handleChatClick(name)}>{chatNameUI(name)}</span>
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
          <button className="signout-button" onClick={() => signout()}>Sign Out</button>
        </header>
        <div className="chat-container">
        {loading ? (
            <div className="loading-indicator">Loading...</div>
          ) : (
            messages.map((msg, index) => {
              let content;
              if (msg.type === 'text') {
                content = <p className="text-type">{msg.content}</p>;
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
            })
          )}
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