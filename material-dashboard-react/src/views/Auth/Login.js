import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import Card from "@mui/material/Card";
import Switch from "@mui/material/Switch";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import axios from "axios";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDInput from "components/MDInput";
import MDButton from "components/MDButton";

// Authentication layout components
import BasicLayout from "layouts/authentication/components/BasicLayout";

// Images
import bgImage from "assets/images/bg-sign-in-basic.jpeg";

import { getApiBase } from "utils/apiConfig";
import { getCurrentUser } from "utils/auth";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // If user is already authenticated with a valid unexpired token, redirect to /fraud
    const user = getCurrentUser();
    if (user) {
      navigate("/fraud", { replace: true });
    }

    // Check for success message from state
    if (location.state && location.state.message) {
      setSuccess(location.state.message);
    }
  }, [navigate, location]);

  const handleSetRememberMe = () => setRememberMe(!rememberMe);
  const handleTogglePassword = () => setShowPassword((prev) => !prev);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    const apiBase = getApiBase();

    try {
      const response = await axios.post(`${apiBase}/api/auth/login`, {
        email,
        password,
      });

      const { access_token, full_name, role, branch } = response.data;

      // Store session details in localStorage
      localStorage.setItem("mifds_token", access_token);
      localStorage.setItem("mifds_user_name", full_name);
      localStorage.setItem("mifds_user_role", role);
      if (branch) localStorage.setItem("mifds_user_branch", branch);

      // Always redirect supervisors to /fraud
      navigate("/fraud", { replace: true });
    } catch (err) {
      console.error("[Auth Error - Login Failed]", err);
      if (err.response && err.response.status === 403) {
        setError(
          "Field agents do not have access to this system. Please contact your branch supervisor."
        );
      } else if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Invalid email or password");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <BasicLayout image={bgImage}>
      <Card>
        <MDBox
          variant="gradient"
          bgColor="info"
          borderRadius="lg"
          coloredShadow="info"
          mx={2}
          mt={-3}
          p={2}
          mb={1}
          textAlign="center"
        >
          <MDTypography variant="h4" fontWeight="medium" color="white" mt={1}>
            MicroInsure Fraud Monitor
          </MDTypography>
          <MDTypography variant="caption" color="white" sx={{ mt: 1, display: "block" }}>
            Supervisor &amp; Branch Manager Access Only
          </MDTypography>
        </MDBox>
        <MDBox pt={4} pb={3} px={3}>
          {error && (
            <MDBox mb={2} textAlign="center">
              <MDTypography variant="button" color="error" fontWeight="medium">
                {error}
              </MDTypography>
            </MDBox>
          )}
          {success && (
            <MDBox mb={2} textAlign="center">
              <MDTypography variant="button" color="success" fontWeight="medium">
                {success}
              </MDTypography>
            </MDBox>
          )}
          <MDBox component="form" role="form" onSubmit={handleSubmit}>
            <MDBox mb={2}>
              <MDInput
                type="email"
                label="Email"
                fullWidth
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </MDBox>
            <MDBox mb={2}>
              <MDInput
                type={showPassword ? "text" : "password"}
                label="Password"
                id="password"
                fullWidth
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        type="button"
                        onClick={handleTogglePassword}
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        edge="end"
                        style={{ color: "#aaa" }}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </MDBox>
            <MDBox display="flex" alignItems="center" ml={-1}>
              <Switch checked={rememberMe} onChange={handleSetRememberMe} />
              <MDTypography
                variant="button"
                fontWeight="regular"
                color="text"
                onClick={handleSetRememberMe}
                sx={{ cursor: "pointer", userSelect: "none", ml: -1 }}
              >
                &nbsp;&nbsp;Remember me
              </MDTypography>
            </MDBox>
            <MDBox mt={4} mb={1}>
              <MDButton
                variant="gradient"
                color="info"
                fullWidth
                type="submit"
                disabled={loading}
                sx={{ touchAction: "manipulation", py: 1.5 }}
              >
                {loading ? "Logging in..." : "log in"}
              </MDButton>
            </MDBox>
            <MDBox mt={3} mb={1} textAlign="center">
              <MDTypography variant="button" color="text">
                Don&apos;t have an account?{" "}
                <MDTypography
                  component={Link}
                  to="/register"
                  variant="button"
                  color="info"
                  fontWeight="medium"
                  textGradient
                >
                  Register
                </MDTypography>
              </MDTypography>
            </MDBox>
          </MDBox>
        </MDBox>
      </Card>
    </BasicLayout>
  );
}

export default Login;
