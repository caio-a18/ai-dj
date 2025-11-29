import { CognitoUserPool, CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';

// Create user pool object
const poolData = {
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID
};

const userPool = new CognitoUserPool(poolData);

export class CognitoService {
  // Sign up with email, password, and username
  static async signUp(username, email, password) {
    return new Promise((resolve) => {
      userPool.signUp(
        email, // Use email as username
        password,
        [
          { Name: 'email', Value: email },
          { Name: 'preferred_username', Value: username }
        ],
        null,
        (err, result) => {
          if (err) {
            resolve({ success: false, error: err.message });
          } else {
            resolve({ success: true, user: result.user });
          }
        }
      );
    });
  }

  // Sign in with email and password
  static async signIn(email, password) {
    return new Promise((resolve) => {
      const authenticationDetails = new AuthenticationDetails({
        Username: email,
        Password: password,
      });

      const cognitoUser = new CognitoUser({
        Username: email,
        Pool: userPool,
      });

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (result) => {
          resolve({ success: true, user: result });
        },
        onFailure: (err) => {
          resolve({ success: false, error: err.message });
        },
      });
    });
  }

  // Sign out
  static async signOut() {
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
      cognitoUser.signOut();
    }
    return { success: true };
  }

  // Get current authenticated user
  static async getCurrentUser() {
    return new Promise((resolve) => {
      const cognitoUser = userPool.getCurrentUser();

      if (!cognitoUser) {
        resolve({ success: false, error: 'No user found' });
        return;
      }

      cognitoUser.getSession((err) => {
        if (err) {
          resolve({ success: false, error: err.message });
          return;
        }

        cognitoUser.getUserAttributes((err, attributes) => {
          if (err) {
            resolve({ success: false, error: err.message });
          } else {
            resolve({ success: true, user: { attributes, username: cognitoUser.getUsername() } });
          }
        });
      });
    });
  }

  // Confirm sign up with verification code
  static async confirmSignUp(email, code) {
    return new Promise((resolve) => {
      const cognitoUser = new CognitoUser({
        Username: email,
        Pool: userPool,
      });

      cognitoUser.confirmRegistration(code, true, (err) => {
        if (err) {
          resolve({ success: false, error: err.message });
        } else {
          resolve({ success: true });
        }
      });
    });
  }

  // Resend verification code
  static async resendSignUp(email) {
    return new Promise((resolve) => {
      const cognitoUser = new CognitoUser({
        Username: email,
        Pool: userPool,
      });

      cognitoUser.resendConfirmationCode((err) => {
        if (err) {
          resolve({ success: false, error: err.message });
        } else {
          resolve({ success: true });
        }
      });
    });
  }
}