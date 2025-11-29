import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../Styles/LoginSignup.css";
import user_icon from "../Components/assets/person.png";
import email_icon from "../Components/assets/email.png";
import password_icon from "../Components/assets/password.png";
import { CognitoService } from "../services/cognitoService";

const LoginSignup = ({ setIsAuthenticated }) => {
  console.log("LoginSignup component rendering");
  const [action, setAction] = useState("Login");
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [verificationRequired, setVerificationRequired] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const navigate = useNavigate();

  // Button click debug
  const handleButtonClick = (buttonType) => {
    console.log(`Button clicked: ${buttonType}`);
    console.log(`Current action: ${action}`);
    console.log(`Form data:`, formData);
  };

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    // Clear error when user starts typing
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
          setVerificationRequired(true);
        } else {
          setErrors({ submit: result.error });
        }
      } else {
        // Login action
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

  const handleVerification = async () => {
    if (!verificationCode.trim()) {
      setErrors({ verification: "Verification code is required" });
      return;
    }

    setIsLoading(true);
    try {
      const result = await CognitoService.confirmSignUp(
        formData.email,
        verificationCode
      );
      if (result.success) {
        // After successful verification, automatically log them in
        const loginResult = await CognitoService.signIn(
          formData.email,
          formData.password
        );
        if (loginResult.success) {
          setIsAuthenticated(true);
          navigate("/home");
        }
      } else {
        setErrors({ verification: result.error });
      }
    } catch (error) {
      setErrors({ verification: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const resendVerificationCode = async () => {
    setIsLoading(true);
    try {
      const result = await CognitoService.resendSignUp(formData.email);
      if (!result.success) {
        setErrors({ verification: "Failed to resend code. Please try again." });
      }
    } catch (error) {
      setErrors({ verification: error.message });
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
    setVerificationRequired(false);
  };

  const switchToLogin = () => {
    setAction("Login");
    setFormData({
      username: "",
      email: "",
      password: "",
    });
    setErrors({});
    setVerificationRequired(false);
  };

  // Verification UI
  if (verificationRequired) {
    return (
      <div className="loginsignup-container">
        <div className="container">
          <div className="header">
            <div className="text">Verify Email</div>
            <div className="underline"></div>
          </div>
          <div className="inputs">
            <div className="input-wrapper">
              <div className="input">
                <input
                  type="text"
                  placeholder="Enter verification code"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                />
              </div>
              {errors.verification && (
                <div className="error-message">{errors.verification}</div>
              )}
            </div>
            <p className="verification-text">
              We sent a verification code to {formData.email}
            </p>
          </div>
          <div className="submit-container">
            <div
              className="submit"
              onClick={handleVerification}
              disabled={isLoading}
            >
              {isLoading ? "Verifying..." : "Verify Email"}
            </div>
            <div
              className="submit gray"
              onClick={resendVerificationCode}
              disabled={isLoading}
            >
              Resend Code
            </div>
          </div>
        </div>
      </div>
    );
  }

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
            <div className="input">
              <img src={password_icon} alt="" />
              <input
                type="password"
                placeholder="Password..."
                value={formData.password}
                onChange={(e) => handleInputChange("password", e.target.value)}
              />
            </div>
            {errors.password && (
              <div className="error-message">{errors.password}</div>
            )}
          </div>
        </div>
        {action === "Sign Up" ? (
          <div></div>
        ) : (
          <div className="forgot-password">
            Forgot Password? <span>Click Here</span>
          </div>
        )}
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
