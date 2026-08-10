import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Card from "@mui/material/Card";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import InputLabel from "@mui/material/InputLabel";
import FormControl from "@mui/material/FormControl";
import FormHelperText from "@mui/material/FormHelperText";
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
  const [role, setRole] = useState("supervisor"); // supervisor or agent
  const [branch, setBranch] = useState("");
  const [languagePref, setLanguagePref] = useState("english"); // english, twi, dagbani
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    // If user is already authenticated with valid unexpired token, redirect
    const user = getCurrentUser();
    if (user) {
      if (user.role === "agent") {
        navigate("/agent-profile", { replace: true });
      } else {
        navigate("/fraud", { replace: true });
      }
    }
  }, [navigate]);

  const validateForm = () => {
    if (!fullName || !email || !password || !confirmPassword || !role) {
      return "Please fill in all required fields.";
    }

    if (role === "agent" && !branch) {
      return "Branch office is required for Field Agents.";
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
        role,
        branch: branch || undefined,
        language_pref: languagePref,
      });

      // Redirect to login with requested success message
      navigate("/login", {
        state: { message: "Account created. Please log in." },
      });
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
            Register to access your role dashboard
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
                type="password"
                label="Password"
                fullWidth
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </MDBox>
            <MDBox mb={2}>
              <MDInput
                type="password"
                label="Confirm Password"
                fullWidth
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </MDBox>

            {/* Dropdown 1: Role Selection */}
            <MDBox mb={2}>
              <FormControl fullWidth size="medium">
                <InputLabel id="role-select-label">I am a</InputLabel>
                <Select
                  labelId="role-select-label"
                  id="role-select"
                  value={role}
                  label="I am a"
                  onChange={(e) => setRole(e.target.value)}
                  required
                  sx={{ height: "44px" }}
                >
                  <MenuItem value="supervisor">Supervisor / Branch Manager</MenuItem>
                  <MenuItem value="agent">Field Agent</MenuItem>
                </Select>
              </FormControl>
            </MDBox>

            {/* Dropdown 2: Branch Selection (Required for Field Agent) */}
            {role === "agent" && (
              <MDBox mb={2}>
                <FormControl fullWidth size="medium">
                  <InputLabel id="branch-select-label">Branch</InputLabel>
                  <Select
                    labelId="branch-select-label"
                    id="branch-select"
                    value={branch}
                    label="Branch"
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
            )}

            {/* Dropdown 3: Customer Call Language Selection */}
            <MDBox mb={2}>
              <FormControl fullWidth size="medium">
                <InputLabel id="language-select-label">Customer Call Language</InputLabel>
                <Select
                  labelId="language-select-label"
                  id="language-select"
                  value={languagePref}
                  label="Customer Call Language"
                  onChange={(e) => setLanguagePref(e.target.value)}
                  sx={{ height: "44px" }}
                >
                  <MenuItem value="english">English</MenuItem>
                  <MenuItem value="twi">Twi</MenuItem>
                  <MenuItem value="dagbani">Dagbani</MenuItem>
                </Select>
                <FormHelperText>
                  This is the language used when calling your customers about missed payments
                </FormHelperText>
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
