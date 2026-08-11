import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Card from "@mui/material/Card";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import InputLabel from "@mui/material/InputLabel";
import FormControl from "@mui/material/FormControl";
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
import bgImage from "assets/images/bg-sign-up-cover.jpeg";
import { getApiBase } from "utils/apiConfig";
import { getCurrentUser } from "utils/auth";

function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [branch, setBranch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    // If supervisor is already authenticated with valid unexpired token, redirect to /fraud
    const user = getCurrentUser();
    if (user) {
      navigate("/fraud", { replace: true });
    }
  }, [navigate]);

  const validateForm = () => {
    if (!fullName || !email || !password || !confirmPassword || !branch) {
      return "Please fill in all required fields.";
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return "Please enter a valid email address.";
    }

    if (password.length < 8) {
      return "Password must be at least 8 characters long.";
    }

    if (password !== confirmPassword) {
      return "Passwords do not match.";
    }

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    const apiBase = getApiBase();

    try {
      await axios.post(`${apiBase}/api/auth/register`, {
        full_name: fullName,
        email,
        password,
        branch,
        role: "supervisor",
      });

      setSuccess("Account created. Please log in.");
      setTimeout(() => {
        navigate("/login", {
          state: { message: "Account created. Please log in." },
        });
      }, 2000);
    } catch (err) {
      console.error("[Auth Error - Registration Failed]", err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to register. Please try again.");
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
          p={3}
          mb={1}
          textAlign="center"
        >
          <MDTypography variant="h4" fontWeight="medium" color="white" mt={1}>
            Join MicroInsure
          </MDTypography>
          <MDTypography variant="caption" color="white" sx={{ mt: 1, display: "block" }}>
            Supervisor &amp; Branch Manager Portal — Internal Use Only
          </MDTypography>
        </MDBox>
        <MDBox pt={3} pb={3} px={3}>
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
                type="text"
                label="Full Name"
                fullWidth
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </MDBox>
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
                autoComplete="new-password"
                required
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        type="button"
                        onClick={() => setShowPassword((prev) => !prev)}
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
            <MDBox mb={2}>
              <MDInput
                type={showConfirmPassword ? "text" : "password"}
                label="Confirm Password"
                id="confirm-password"
                fullWidth
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        type="button"
                        onClick={() => setShowConfirmPassword((prev) => !prev)}
                        aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                        edge="end"
                        style={{ color: "#aaa" }}
                      >
                        {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </MDBox>

            {/* Branch Selection Dropdown */}
            <MDBox mb={2}>
              <FormControl fullWidth size="medium">
                <InputLabel id="branch-select-label">Your Branch Office</InputLabel>
                <Select
                  labelId="branch-select-label"
                  id="branch-select"
                  value={branch}
                  label="Your Branch Office"
                  onChange={(e) => setBranch(e.target.value)}
                  required
                  sx={{ height: "44px" }}
                >
                  <MenuItem value="Accra">Accra</MenuItem>
                  <MenuItem value="Kumasi">Kumasi</MenuItem>
                  <MenuItem value="Tamale">Tamale</MenuItem>
                  <MenuItem value="Takoradi">Takoradi</MenuItem>
                  <MenuItem value="Cape_Coast">Cape Coast</MenuItem>
                </Select>
              </FormControl>
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
                {loading ? "Registering..." : "register"}
              </MDButton>
            </MDBox>

            <MDBox mt={3} mb={1} textAlign="center">
              <MDTypography variant="button" color="text">
                Already have an account?{" "}
                <MDTypography
                  component={Link}
                  to="/login"
                  variant="button"
                  color="info"
                  fontWeight="medium"
                  textGradient
                >
                  Log in
                </MDTypography>
              </MDTypography>
            </MDBox>
          </MDBox>
        </MDBox>
      </Card>
    </BasicLayout>
  );
}

export default Register;
