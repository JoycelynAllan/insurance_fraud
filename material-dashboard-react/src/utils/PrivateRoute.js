import React from "react";
import { Navigate } from "react-router-dom";
import PropTypes from "prop-types";
import { getCurrentUser } from "./auth";

/**
 * Role-Based Route Guard Wrapper Component.
 * - Redirects unauthenticated users to /login.
 * - Restricts agents from accessing supervisor routes (/fraud, /voice-campaigns).
 */
function PrivateRoute({ children, allowedRoles }) {
  const token = localStorage.getItem("mifds_token");
  const user = getCurrentUser();

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  const userRole = user.role || localStorage.getItem("mifds_user_role") || "supervisor";

  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
    if (userRole === "agent") {
      return <Navigate to="/agent-profile" replace />;
    }
    return <Navigate to="/fraud" replace />;
  }

  return children;
}

PrivateRoute.propTypes = {
  children: PropTypes.node.isRequired,
  allowedRoles: PropTypes.arrayOf(PropTypes.string),
};

PrivateRoute.defaultProps = {
  allowedRoles: [],
};

export default PrivateRoute;
