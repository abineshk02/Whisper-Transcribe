import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post("http://127.0.0.1:8000/auth/login", {
        username,
        password,
      });

      if (response.status === 200) {
        // Navigate to Transcribe page after successful login
        navigate("/transcribe");
      }
    } catch (err) {
      if (err.response) {
        setMessage(err.response.data.detail || "Login failed");
      } else {
        setMessage("Error connecting to server");
      }
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <div>
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Login</button>
      </form>
      <p>{message}</p>
      <p>
        Not registered?{" "}
        <button onClick={() => navigate("/signup")}>Signup here</button>
      </p>
    </div>
  );
};

export default LoginPage;
