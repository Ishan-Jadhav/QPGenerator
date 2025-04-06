import { Routes, Route } from 'react-router-dom';
import './App.css';
import ChatPage from './pages/ChatPage';
import CreateDatabasePage from './pages/CreateDatabasePage';

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/create-database" element={<CreateDatabasePage />} />
      </Routes>
    </div>
  );
}

export default App;
