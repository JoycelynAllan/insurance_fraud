import React, { useState, useEffect } from "react";
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
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Icon from "@mui/material/Icon";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDBadge from "components/MDBadge";
import MDButton from "components/MDButton";

// Material Dashboard 2 React example components
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";

import { getApiBase } from "utils/apiConfig";

import toast from "react-hot-toast";

function VoiceCampaigns() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Manual Trigger Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [manualPhone, setManualPhone] = useState("");
  const [manualAgent, setManualAgent] = useState("AGT041");
  const [manualAmount, setManualAmount] = useState("150.0");
  const [manualLanguage, setManualLanguage] = useState("english");
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [triggerSuccess, setTriggerSuccess] = useState("");

  const fetchLogs = async () => {
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const response = await axios.get(`${apiBase}/api/voice/logs`, { headers });
      const rawLogs = Array.isArray(response.data) ? response.data : response.data.logs || [];
      const totalCount = Array.isArray(response.data)
        ? response.data.length
        : response.data.total || rawLogs.length;
      setLogs(rawLogs);
      setTotal(totalCount);
    } catch (err) {
      console.error("Error fetching voice campaign logs:", err);
      setError("Failed to connect to the Voice Campaigns backend service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    // Auto refresh every 30 seconds
    const interval = setInterval(fetchLogs, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerSubmit = async (e) => {
    e.preventDefault();
    setTriggerLoading(true);
    setTriggerSuccess("");

    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      await axios.post(
        `${apiBase}/api/voice/trigger`,
        {
          customer_phone: manualPhone,
          agent_id: manualAgent,
          amount: parseFloat(manualAmount) || 150.0,
          language: manualLanguage,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success("Manual call scheduled successfully!");
      fetchLogs();
      setModalOpen(false);
      setManualPhone("");
    } catch (err) {
      console.error("Failed to trigger manual voice reminder call:", err);
      toast.error("Failed to schedule call. Please try again.");
    } finally {
      setTriggerLoading(false);
    }
  };

  const getOutcomeBadge = (outcome) => {
    const val = (outcome || "").toLowerCase();
    switch (val) {
      case "sent":
        return <MDBadge badgeContent="Sent" color="success" variant="gradient" size="xs" />;
      case "failed":
        return <MDBadge badgeContent="Failed" color="error" variant="gradient" size="xs" />;
      case "payment_confirmed_by_customer":
        return <MDBadge badgeContent="Confirmed" color="info" variant="gradient" size="xs" />;
      case "transfer_to_support_requested":
        return <MDBadge badgeContent="Support Req" color="warning" variant="gradient" size="xs" />;
      case "max_retries_reached":
        return (
          <MDBadge badgeContent="Max Retries" color="secondary" variant="gradient" size="xs" />
        );
      default:
        return (
          <MDBadge badgeContent={outcome || "Queued"} color="info" variant="gradient" size="xs" />
        );
    }
  };

  const formatTimestamp = (ts) => {
    if (!ts) return "-";
    try {
      const date = new Date(ts);
      return date.toLocaleString();
    } catch (e) {
      return ts;
    }
  };

  // Metrics summary row calculations
  const totalCalls = logs.length;
  const confirmedPayments = logs.filter(
    (l) => l.outcome === "payment_confirmed_by_customer"
  ).length;
  const failedCalls = logs.filter((l) => l.outcome === "failed").length;
  const pendingRetries = logs.filter((l) => l.outcome === "sent" || l.outcome === "queued").length;

  return (
    <DashboardLayout>
      <DashboardNavbar title="Voice Campaigns" showGhanaTime />
      <MDBox py={3}>
        {/* Summary Metrics Cards Row */}
        <MDBox mb={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ p: 2, textAlign: "center" }}>
                <MDTypography variant="button" color="text" fontWeight="medium">
                  Total Calls Made
                </MDTypography>
                <MDTypography variant="h3" fontWeight="bold" color="dark" mt={1}>
                  {totalCalls}
                </MDTypography>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ p: 2, textAlign: "center" }}>
                <MDTypography variant="button" color="text" fontWeight="medium">
                  Confirmed Payments
                </MDTypography>
                <MDTypography variant="h3" fontWeight="bold" color="info" mt={1}>
                  {confirmedPayments}
                </MDTypography>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ p: 2, textAlign: "center" }}>
                <MDTypography variant="button" color="text" fontWeight="medium">
                  Failed Calls
                </MDTypography>
                <MDTypography variant="h3" fontWeight="bold" color="error" mt={1}>
                  {failedCalls}
                </MDTypography>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ p: 2, textAlign: "center" }}>
                <MDTypography variant="button" color="text" fontWeight="medium">
                  Pending Retries
                </MDTypography>
                <MDTypography variant="h3" fontWeight="bold" color="warning" mt={1}>
                  {pendingRetries}
                </MDTypography>
              </Card>
            </Grid>
          </Grid>
        </MDBox>

        {/* Main Table Card */}
        <MDBox mb={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <MDBox
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  mx={2}
                  mt={-3}
                  py={2}
                  px={2}
                  variant="gradient"
                  bgColor="info"
                  borderRadius="lg"
                  coloredShadow="info"
                >
                  <MDBox>
                    <MDTypography variant="h6" color="white">
                      Voice & SMS Telephony Campaign Logs
                    </MDTypography>
                    <MDTypography variant="caption" color="white" opacity={0.8}>
                      Automated & Manual Reminders (Auto-refreshes every 30s)
                    </MDTypography>
                  </MDBox>
                  <MDBox display="flex" gap={1}>
                    <MDButton
                      variant="gradient"
                      color="dark"
                      size="small"
                      onClick={() => setModalOpen(true)}
                    >
                      <Icon sx={{ mr: 0.5 }}>phone_in_talk</Icon> Trigger Manual Call
                    </MDButton>
                    <MDButton variant="outlined" color="white" size="small" onClick={fetchLogs}>
                      <Icon sx={{ mr: 0.5 }}>refresh</Icon> Refresh
                    </MDButton>
                  </MDBox>
                </MDBox>

                {/* Table Content */}
                <MDBox pt={3} px={2} pb={3}>
                  {loading ? (
                    <MDBox display="flex" justifyContent="center" py={8}>
                      <CircularProgress color="info" />
                    </MDBox>
                  ) : error ? (
                    <MDBox textAlign="center" py={6}>
                      <MDTypography variant="body2" color="error" mb={2}>
                        {error}
                      </MDTypography>
                      <MDButton variant="gradient" color="info" size="small" onClick={fetchLogs}>
                        Retry
                      </MDButton>
                    </MDBox>
                  ) : logs.length === 0 ? (
                    <MDBox textAlign="center" py={6}>
                      <MDTypography variant="body2" color="text">
                        No voice campaign logs found.
                      </MDTypography>
                    </MDBox>
                  ) : (
                    <TableContainer>
                      <Table size="small">
                        <TableHead sx={{ display: "table-header-group" }}>
                          <TableRow>
                            <TableCell sx={{ fontWeight: "bold" }}>Customer Phone</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Agent ID</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Amount (GHS)</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Language</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Attempt Number</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Outcome</TableCell>
                            <TableCell sx={{ fontWeight: "bold" }}>Timestamp</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {logs.map((log) => (
                            <TableRow key={log.id} hover>
                              <TableCell>
                                <MDTypography variant="button" fontWeight="medium">
                                  {log.customer_phone}
                                </MDTypography>
                              </TableCell>
                              <TableCell>{log.agent_id}</TableCell>
                              <TableCell>
                                GHS{" "}
                                {typeof log.amount === "number"
                                  ? log.amount.toFixed(2)
                                  : log.amount}
                              </TableCell>
                              <TableCell>
                                {(log.language_pref || "english").toUpperCase()}
                              </TableCell>
                              <TableCell>{log.attempt_number || 1}</TableCell>
                              <TableCell>{getOutcomeBadge(log.outcome)}</TableCell>
                              <TableCell>
                                {formatTimestamp(log.called_at || log.timestamp)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </MDBox>
              </Card>
            </Grid>
          </Grid>
        </MDBox>
      </MDBox>

      {/* Manual Trigger Modal Dialog */}
      <Dialog open={modalOpen} onClose={() => setModalOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Trigger Manual Voice Call</DialogTitle>
        <form onSubmit={handleTriggerSubmit}>
          <DialogContent>
            {triggerSuccess && (
              <MDTypography
                variant="caption"
                color="success"
                fontWeight="bold"
                display="block"
                mb={2}
              >
                {triggerSuccess}
              </MDTypography>
            )}
            <MDBox mb={2}>
              <TextField
                fullWidth
                label="Customer Phone Number"
                value={manualPhone}
                onChange={(e) => setManualPhone(e.target.value)}
                placeholder="+233200000000"
                required
              />
            </MDBox>
            <MDBox mb={2}>
              <TextField
                fullWidth
                label="Agent ID"
                value={manualAgent}
                onChange={(e) => setManualAgent(e.target.value)}
                required
              />
            </MDBox>
            <MDBox mb={2}>
              <TextField
                fullWidth
                label="Amount (GHS)"
                type="number"
                value={manualAmount}
                onChange={(e) => setManualAmount(e.target.value)}
                required
              />
            </MDBox>
            <MDBox mb={2}>
              <FormControl fullWidth>
                <InputLabel id="manual-lang-label">Customer Call Language</InputLabel>
                <Select
                  labelId="manual-lang-label"
                  value={manualLanguage}
                  label="Customer Call Language"
                  onChange={(e) => setManualLanguage(e.target.value)}
                  sx={{ height: "44px" }}
                >
                  <MenuItem value="english">English</MenuItem>
                  <MenuItem value="twi">Twi</MenuItem>
                  <MenuItem value="dagbani">Dagbani</MenuItem>
                </Select>
              </FormControl>
            </MDBox>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <MDButton color="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </MDButton>
            <MDButton type="submit" color="info" disabled={triggerLoading}>
              {triggerLoading ? "Scheduling..." : "Schedule Call"}
            </MDButton>
          </DialogActions>
        </form>
      </Dialog>

      <Footer />
    </DashboardLayout>
  );
}

export default VoiceCampaigns;
