import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

// @mui material components
import Card from "@mui/material/Card";
import Grid from "@mui/material/Grid";
import TableContainer from "@mui/material/TableContainer";
import Table from "@mui/material/Table";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import TableBody from "@mui/material/TableBody";
import CircularProgress from "@mui/material/CircularProgress";
import Icon from "@mui/material/Icon";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDBadge from "components/MDBadge";

// Material Dashboard 2 React example components
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";

import { getApiBase } from "utils/apiConfig";

function AgentProfile() {
  const { agentId: routeAgentId } = useParams();
  const [profile, setProfile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [riskScore, setRiskScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const currentUserName = localStorage.getItem("mifds_user_name") || "Field Agent";
  const currentUserBranch = localStorage.getItem("mifds_user_branch") || "Tamale";
  const userAgentId = routeAgentId || localStorage.getItem("mifds_user_agent_id") || "AGT041";

  useEffect(() => {
    const fetchAgentData = async () => {
      setLoading(true);
      setError("");
      try {
        const apiBase = getApiBase();
        const token = localStorage.getItem("mifds_token");
        const headers = { Authorization: `Bearer ${token}` };

        // Fetch user profile info
        const meRes = await axios.get(`${apiBase}/api/auth/me`, { headers });
        setProfile(meRes.data);

        // Fetch agent transactions
        const txRes = await axios.get(`${apiBase}/api/agents/${userAgentId}/transactions`, { headers });
        const txList = Array.isArray(txRes.data) ? txRes.data : [];
        setTransactions(txList);

        if (txList.length > 0) {
          const latestScore = txList[0].risk_score;
          setRiskScore(typeof latestScore === "number" ? latestScore : 0);
        }
      } catch (err) {
        console.error("Error fetching agent profile:", err);
        if (err.response && err.response.data && err.response.data.detail) {
          setError(err.response.data.detail);
        } else {
          setError("Failed to load agent profile data.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAgentData();
  }, [userAgentId]);

  const getScoreColor = (score) => {
    const val = score <= 1.0 ? score * 100 : score;
    if (val < 40) return "success.main";
    if (val < 70) return "warning.main";
    return "error.main";
  };

  const getStatusBadge = (statusStr) => {
    switch ((statusStr || "").toLowerCase()) {
      case "remitted":
      case "settled":
        return <MDBadge badgeContent="Remitted" color="success" variant="gradient" size="xs" />;
      case "pending":
        return <MDBadge badgeContent="Pending" color="warning" variant="gradient" size="xs" />;
      case "missed":
      case "flagged":
        return <MDBadge badgeContent="Missed" color="error" variant="gradient" size="xs" />;
      default:
        return <MDBadge badgeContent={statusStr || "Normal"} color="secondary" variant="gradient" size="xs" />;
    }
  };

  const scorePct = riskScore <= 1.0 ? riskScore * 100 : riskScore;

  return (
    <DashboardLayout>
      <DashboardNavbar title="My Agent Profile" showGhanaTime />
      <MDBox py={3}>
        <MDBox mb={3}>
          <Grid container spacing={3}>

            {/* Welcome & Overview Banner Card */}
            <Grid item xs={12} md={8}>
              <Card sx={{ height: "100%", p: 3 }}>
                <MDBox display="flex" alignItems="center" mb={2}>
                  <Icon sx={{ fontSize: "32px !important", color: "info.main", mr: 1.5 }}>
                    account_circle
                  </Icon>
                  <MDBox>
                    <MDTypography variant="h5" fontWeight="bold">
                      Welcome, {profile?.full_name || currentUserName}
                    </MDTypography>
                    <MDTypography variant="button" color="text">
                      Branch: <strong>{profile?.branch || currentUserBranch}</strong> | Role: <strong>Field Agent</strong> | ID: <strong>{userAgentId}</strong>
                    </MDTypography>
                  </MDBox>
                </MDBox>
                <MDTypography variant="body2" color="text" sx={{ mt: 1 }}>
                  Customer Call Language: <strong>{(profile?.language_pref || "english").toUpperCase()}</strong>
                </MDTypography>
              </Card>
            </Grid>

            {/* Large Risk Score Display Card */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: "100%", p: 3, textAlign: "center" }}>
                <MDTypography variant="button" color="text" fontWeight="medium">
                  Your Current Risk Score
                </MDTypography>
                <MDTypography
                  variant="h1"
                  fontWeight="bold"
                  sx={{ color: getScoreColor(riskScore), my: 1, fontSize: "3.5rem" }}
                >
                  {scorePct.toFixed(1)}%
                </MDTypography>
                <MDTypography variant="caption" color="text">
                  {scorePct < 40
                    ? "Normal — Low Operational Risk"
                    : scorePct < 70
                    ? "Moderate — Remittance Review Pending"
                    : "High Risk — Missed Remittance Flagged"}
                </MDTypography>
              </Card>
            </Grid>

            {/* Transaction Table Card */}
            <Grid item xs={12}>
              <Card>
                <MDBox
                  mx={2}
                  mt={-3}
                  py={2}
                  px={2}
                  variant="gradient"
                  bgColor="info"
                  borderRadius="lg"
                  coloredShadow="info"
                >
                  <MDTypography variant="h6" color="white">
                    My Transaction History ({transactions.length})
                  </MDTypography>
                </MDBox>
                <MDBox pt={3} px={2} pb={3}>
                  {loading ? (
                    <MDBox display="flex" justifyContent="center" py={6}>
                      <CircularProgress color="info" />
                    </MDBox>
                  ) : error ? (
                    <MDBox textAlign="center" py={4}>
                      <MDTypography variant="button" color="error" fontWeight="medium">
                        {error}
                      </MDTypography>
                    </MDBox>
                  ) : transactions.length === 0 ? (
                    <MDBox textAlign="center" py={4}>
                      <MDTypography variant="button" color="text">
                        No transactions recorded for this account.
                      </MDTypography>
                    </MDBox>
                  ) : (
                    <TableContainer>
                      <Table size="small">
                        <TableHead sx={{ display: "table-header-group" }}>
                          <TableRow>
                            <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Customer Phone</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Amount (GHS)</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Payment Method</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Remittance Status</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {transactions.map((tx) => (
                            <TableRow key={tx.id} hover>
                              <TableCell>{tx.date || tx.timestamp}</TableCell>
                              <TableCell>{tx.customer_phone || "-"}</TableCell>
                              <TableCell>GHS {typeof tx.amount === "number" ? tx.amount.toFixed(2) : tx.amount}</TableCell>
                              <TableCell>{tx.payment_method || "Cash"}</TableCell>
                              <TableCell>{getStatusBadge(tx.remittance_status)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}

                  {/* Informational Disclaimer Message */}
                  <MDBox mt={3} p={2} borderRadius="md" sx={{ backgroundColor: "rgba(2, 136, 209, 0.08)", border: "1px dashed #0288d1" }}>
                    <MDTypography variant="caption" color="info" fontWeight="medium">
                      ℹ️ If you believe your risk score is incorrect, please contact your branch supervisor.
                    </MDTypography>
                  </MDBox>
                </MDBox>
              </Card>
            </Grid>

          </Grid>
        </MDBox>
      </MDBox>
      <Footer />
    </DashboardLayout>
  );
}

export default AgentProfile;
