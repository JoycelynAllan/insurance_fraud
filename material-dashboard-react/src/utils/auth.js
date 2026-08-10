/**
 * Safely parses and validates a JWT access token.
 * Checks token expiration (exp claim) and clears stale localStorage if expired or invalid.
 */
export function parseJwt(token) {
  if (!token) return null;
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) return null;
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const parsed = JSON.parse(jsonPayload);

    // Check if token is expired (exp is in seconds)
    if (parsed.exp && parsed.exp * 1000 < Date.now()) {
      localStorage.removeItem("mifds_token");
      localStorage.removeItem("mifds_user_name");
      localStorage.removeItem("mifds_user_role");
      localStorage.removeItem("mifds_user_branch");
      localStorage.removeItem("mifds_user_agent_id");
      return null;
    }
    return parsed;
  } catch (err) {
    localStorage.removeItem("mifds_token");
    localStorage.removeItem("mifds_user_name");
    localStorage.removeItem("mifds_user_role");
    localStorage.removeItem("mifds_user_branch");
    localStorage.removeItem("mifds_user_agent_id");
    return null;
  }
}

export function getCurrentUser() {
  const token = localStorage.getItem("mifds_token");
  if (!token) return null;
  const user = parseJwt(token);
  if (!user) return null;
  return {
    ...user,
    role: user.role || localStorage.getItem("mifds_user_role") || "supervisor",
    full_name: localStorage.getItem("mifds_user_name") || "User",
  };
}
