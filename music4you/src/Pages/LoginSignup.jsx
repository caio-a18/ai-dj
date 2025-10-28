import {useState} from "react";
import { useNavigate } from "react-router-dom";
import "../Styles/LoginSignup.css";
import user_icon from "../Components/assets/person.png";
import email_icon from "../Components/assets/email.png";
import password_icon from "../Components/assets/password.png";

const LoginSignup = ({ setIsAuthenticated }) => {
  const [action, setAction] = useState("Login");
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: ""
  });
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ""
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (action === "Sign Up" && !formData.username.trim()) {
      newErrors.username = "Username is required";
    }
    
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid";
    }
    
    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      // Simulate successful authentication
      setIsAuthenticated(true);
      navigate("/home");
    }
  };

  const switchToSignUp = () => {
    setAction("Sign Up");
    setFormData({
      username: "",
      email: "",
      password: ""
    });
    setErrors({});
  };

  const switchToLogin = () => {
    setAction("Login");
    setFormData({
      username: "",
      email: "",
      password: ""
    });
    setErrors({});
  };

  return (
    <div className="loginsignup-container">
      <div className="container">
        <div className="header">
          <div className="text">{action}</div>
          <div className="underline"></div>
        </div>
        <div className="inputs">
          {action==="Login"?<div></div>:<div className="input-wrapper">
            <div className="input">
              <img src={user_icon} alt="" />
              <input 
                type="text" 
                placeholder="Username" 
                value={formData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
              />
            </div>
            {errors.username && <div className="error-message">{errors.username}</div>}
          </div>}
          
          <div className="input-wrapper">
            <div className="input">
              <img src={email_icon} alt="" />
              <input 
                type="email" 
                placeholder="Email" 
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
              />
            </div>
            {errors.email && <div className="error-message">{errors.email}</div>}
          </div>

          <div className="input-wrapper">
            <div className="input">
              <img src={password_icon} alt="" />
              <input 
                type="password" 
                placeholder="Password..." 
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
              />
            </div>
            {errors.password && <div className="error-message">{errors.password}</div>}
          </div>
        </div>
        {action==="Sign Up"?<div></div>:<div className="forgot-password">
          Forgot Password? <span>Click Here</span>
        </div>}
        <div className="submit-container">
          <div 
            className={action === "Login" ? "submit gray" : "submit"} 
            onClick={action === "Login" ? switchToSignUp : handleSubmit}
          >
            Sign Up
          </div>
          <div 
            className={action === "Sign Up" ? "submit gray" : "submit"} 
            onClick={action === "Sign Up" ? switchToLogin : handleSubmit}
          >
            Login
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginSignup;