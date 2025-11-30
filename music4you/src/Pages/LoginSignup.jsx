import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../Styles/LoginSignup.css";
import user_icon from "../Components/assets/person.png";
import email_icon from "../Components/assets/email.png";
import password_icon from "../Components/assets/password.png";
import closed_eye from "../Components/assets/pwrd_closed_eye.png";
import open_eye from "../Components/assets/pwrd_open_eye.png";
import { CognitoService } from "../services/cognitoService";

const LoginSignup = ({ setIsAuthenticated }) => {
  const [action, setAction] = useState("Login");
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  // Toggle password visibility
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: "",
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

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    setErrors({});

    try {
      if (action === "Sign Up") {
        const result = await CognitoService.signUp(
          formData.username,
          formData.email,
          formData.password
        );

        if (result.success) {
          const loginResult = await CognitoService.signIn(
            formData.email,
            formData.password
          );
          
          if (loginResult.success) {
            setIsAuthenticated(true);
            navigate("/home");
          } else {
            setErrors({ submit: loginResult.error });
          }
        } else {
          setErrors({ submit: result.error });
        }
      } else {
        const result = await CognitoService.signIn(
          formData.email,
          formData.password
        );

        if (result.success) {
          setIsAuthenticated(true);
          navigate("/home");
        } else {
          setErrors({ submit: result.error });
        }
      }
    } catch (error) {
      setErrors({ submit: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const switchToSignUp = () => {
    setAction("Sign Up");
    setFormData({
      username: "",
      email: "",
      password: "",
    });
    setErrors({});
  };

  const switchToLogin = () => {
    setAction("Login");
    setFormData({
      username: "",
      email: "",
      password: "",
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
          {action === "Login" ? (
            <div></div>
          ) : (
            <div className="input-wrapper">
              <div className="input">
                <img src={user_icon} alt="" />
                <input
                  type="text"
                  placeholder="Username"
                  value={formData.username}
                  onChange={(e) =>
                    handleInputChange("username", e.target.value)
                  }
                />
              </div>
              {errors.username && (
                <div className="error-message">{errors.username}</div>
              )}
            </div>
          )}

          <div className="input-wrapper">
            <div className="input">
              <img src={email_icon} alt="" />
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
              />
            </div>
            {errors.email && (
              <div className="error-message">{errors.email}</div>
            )}
          </div>

          <div className="input-wrapper">
            <div className="input password-input">
              <img src={password_icon} alt="" />
              <input
                type={showPassword ? "text" : "password"} // Toggle input type
                placeholder="Password..."
                value={formData.password}
                onChange={(e) => handleInputChange("password", e.target.value)}
              />
              <img 
                src={showPassword ? open_eye : closed_eye} // Toggle eye icon
                alt={showPassword ? "Hide password" : "Show password"}
                className="eye-icon"
                onClick={togglePasswordVisibility}
              />
            </div>
            {errors.password && (
              <div className="error-message">{errors.password}</div>
            )}
          </div>
        </div>

        {errors.submit && (
          <div className="error-message submit-error">{errors.submit}</div>
        )}

        {/* Removed forgot password section */}

        <div className="submit-container">
          <div
            className={action === "Login" ? "submit gray" : "submit"}
            onClick={action === "Login" ? switchToSignUp : handleSubmit}
          >
            {isLoading ? "Loading..." : "Sign Up"}
          </div>
          <div
            className={action === "Sign Up" ? "submit gray" : "submit"}
            onClick={action === "Sign Up" ? switchToLogin : handleSubmit}
          >
            {isLoading ? "Loading..." : "Login"}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginSignup;