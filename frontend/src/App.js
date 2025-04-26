import { Routes, Route } from 'react-router-dom';
import './App.css';
import ChatPage from './pages/ChatPage';
import CreateDatabasePage from './pages/CreateDatabasePage';
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/create-database" element={<CreateDatabasePage />} />
        <Route path="/signin" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
      </Routes>
    </div>
  );
}

export default App;
