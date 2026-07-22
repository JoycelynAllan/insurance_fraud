import React from "react";
import { Navigate } from "react-router-dom";
import PropTypes from "prop-types";

/**
 * Route guard wrapper component.
 * Redirects the user to the login screen if the authentication token is missing.
 */
function PrivateRoute({ children }) {
  const token = localStorage.getItem("mifds_token");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

PrivateRoute.propTypes = {
  children: PropTypes.node.isRequired,
};

export default PrivateRoute;
