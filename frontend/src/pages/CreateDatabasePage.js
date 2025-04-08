import React, { useState } from 'react';
import './CreateDatabasePage.css';
import { useNavigate } from 'react-router-dom';
function CreateDatabasePage() {
  const [dbName, setDbName] = useState('');
  const [tableFiles, setTableFiles] = useState([]);
  const [metadataFile, setMetadataFile] = useState(null);
  const navigate = useNavigate();
  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("db_name", dbName);
    formData.append("metadata_file", metadataFile);
    tableFiles.forEach((file, idx) => {
      formData.append("table_files", file); // FastAPI can handle lists
    });

    try {
      const response = await fetch("http://localhost:8000/upload-database", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      console.log("Server response:", result);
      navigate("/")
    } catch (err) {
      console.error("Error uploading:", err);
    }
  };

  return (
    <div className="create-database-page">
      <h1>Create Database</h1>
      <form onSubmit={handleSubmit} className="create-database-form">
        <div className="form-group">
          <label>Database Name:</label>
          <input
            type="text"
            value={dbName}
            onChange={(e) => setDbName(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Table Files:</label>
          <input
            type="file"
            multiple
            onChange={(e) => setTableFiles(Array.from(e.target.files))}
            required
          />
        </div>
        <div className="form-group">
          <label>Metadata File:</label>
          <input
            type="file"
            onChange={(e) => setMetadataFile(e.target.files[0])}
            required
          />
        </div>
        <button type="submit">Create</button>
      </form>
    </div>
  );
}

export default CreateDatabasePage;
