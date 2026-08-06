/**
 * Utility functions for resolving API base URLs and WebSocket URLs in production and development.
 */

export const getApiBase = () => {
  const url =
    process.env.REACT_APP_API_URL || process.env.REACT_APP_API_BASE || "http://localhost:8000";
  return url.trim().replace(/\/$/, "");
};

export const getWsBase = () => {
  if (process.env.REACT_APP_WS_URL) {
    return process.env.REACT_APP_WS_URL.trim().replace(/\/$/, "");
  }
  const apiBase = getApiBase();
  return apiBase.replace(/^http/, "ws");
};
