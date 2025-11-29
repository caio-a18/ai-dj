export const cognitoConfig = {
  authority: `https://cognito-idp.${import.meta.env.VITE_COGNITO_REGION}.amazonaws.com/${import.meta.env.VITE_COGNITO_USER_POOL_ID}`,
  client_id: import.meta.env.VITE_COGNITO_CLIENT_ID,
  redirect_uri: import.meta.env.VITE_REDIRECT_URI,
  response_type: "code",
  scope: "phone openid email profile",
  automaticSilentRenew: true,
  loadUserInfo: true,
}

// For local development, you might want a different redirect_uri
export const getConfig = () => {
  const isLocal = window.location.hostname === 'localhost';
  
  return {
    ...cognitoConfig,
    redirect_uri: isLocal ? 'http://localhost:5173' : cognitoConfig.redirect_uri,
  };
};