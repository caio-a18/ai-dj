import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from "amazon-cognito-identity-js";

const poolData = {
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
};

const userPool = new CognitoUserPool(poolData);

export class CognitoService {
  static async signUp(username, email, password) {
    return new Promise((resolve) => {
      userPool.signUp(
        email,
        password,
        [
          { Name: "email", Value: email },
          { Name: "custom:username", Value: username },
        ],
        null,
        (err, result) => {
          if (err) {
            resolve({ success: false, error: err.message });
          } else {
            resolve({
              success: true,
              user: result.user,
            });
          }
        }
      );
    });
  }

  static async getUserAttributes() {
    return new Promise((resolve) => {
      const cognitoUser = userPool.getCurrentUser();

      if (!cognitoUser) {
        resolve({ success: false, error: "No user found" });
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
            // Convert attributes to a more usable format
            const userAttributes = {};
            attributes.forEach((attr) => {
              userAttributes[attr.Name] = attr.Value;
            });
            resolve({ success: true, attributes: userAttributes });
          }
        });
      });
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
    
    // Clear Spotify tokens when logging out of Cognito
    try {
      sessionStorage.removeItem('spotify_tokens');
      sessionStorage.removeItem('spotify_auth_in_progress');
      window.dispatchEvent(new Event('spotify-disconnected'));
    } catch (e) {
      console.warn('Error clearing Spotify tokens on logout', e);
    }
    
    return { success: true };
  }

  // Get current authenticated user
  static async getCurrentUser() {
    return new Promise((resolve) => {
      const cognitoUser = userPool.getCurrentUser();

      if (!cognitoUser) {
        resolve({ success: false, error: "No user found" });
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
            resolve({
              success: true,
              user: { attributes, username: cognitoUser.getUsername() },
            });
          }
        });
      });
    });
  }

  // These can be empty since we don't need verification
  static async confirmSignUp() {
    return { success: true };
  }

  static async resendSignUp() {
    return { success: true };
  }
}
