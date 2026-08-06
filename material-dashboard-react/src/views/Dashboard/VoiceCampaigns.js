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

function VoiceCampaigns() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters and Pagination state
  const [agentFilter, setAgentFilter] = useState("");
  const [outcomeFilter, setOutcomeFilter] = useState("all");
  const [page, setPage] = useState(0);
  const limit = 10;

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const params = {
        limit,
        offset: page * limit,
      };

      if (agentFilter.trim()) {
        params.agent_id = agentFilter.trim();
      }
      if (outcomeFilter && outcomeFilter !== "all") {
        params.outcome = outcomeFilter;
      }

      const response = await axios.get(`${apiBase}/api/voice/logs`, {
        headers,
        params,
      });

      setLogs(response.data.logs || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      console.error("Error fetching voice campaign logs:", err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(`Error: ${err.response.data.detail}`);
      } else {
        setError("Failed to connect to the Voice Campaigns backend service.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, outcomeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(0);
    fetchLogs();
  };

  const getOutcomeBadge = (outcome) => {
    switch (outcome ? outcome.toLowerCase() : "") {
      case "answered":
      case "completed":
        return <MDBadge badgeContent="Answered" color="success" variant="gradient" size="xs" />;
      case "no_answer":
      case "busy":
      case "timeout":
        return <MDBadge badgeContent="No Answer" color="warning" variant="gradient" size="xs" />;
      case "failed":
        return <MDBadge badgeContent="Failed" color="error" variant="gradient" size="xs" />;
      default:
        return (
          <MDBadge
            badgeContent={outcome || "Unknown"}
            color="secondary"
            variant="gradient"
            size="xs"
          />
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

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <DashboardLayout>
      <DashboardNavbar title="Voice Campaigns" showGhanaTime />
      <MDBox py={3}>
        <MDBox mb={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                {/* Header card banner */}
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
                      Voice Campaigns Activity Logs
                    </MDTypography>
                    <MDTypography variant="caption" color="white" opacity={0.8}>
                      Automated & Manual Outbound Telephony Payment Reminders (Dograh Integration)
                    </MDTypography>
                  </MDBox>
                  <MDButton variant="gradient" color="dark" size="small" onClick={fetchLogs}>
                    <Icon sx={{ mr: 0.5 }}>refresh</Icon> Refresh
                  </MDButton>
                </MDBox>

                {/* Filters Row */}
                <MDBox
                  pt={3}
                  px={3}
                  pb={1}
                  display="flex"
                  flexWrap="wrap"
                  gap={2}
                  alignItems="center"
                >
                  <form
                    onSubmit={handleSearchSubmit}
                    style={{ display: "flex", gap: "16px", alignItems: "center" }}
                  >
                    <TextField
                      size="small"
                      label="Filter by Agent ID"
                      variant="outlined"
                      value={agentFilter}
                      onChange={(e) => setAgentFilter(e.target.value)}
                      placeholder="e.g. AGT035"
                      sx={{ width: "200px" }}
                    />
                    <MDButton type="submit" variant="outlined" color="info" size="small">
                      Filter
                    </MDButton>
                  </form>

                  <FormControl size="small" sx={{ minWidth: 180 }}>
                    <InputLabel id="outcome-select-label">Outcome Filter</InputLabel>
                    <Select
                      labelId="outcome-select-label"
                      value={outcomeFilter}
                      label="Outcome Filter"
                      onChange={(e) => {
                        setOutcomeFilter(e.target.value);
                        setPage(0);
                      }}
                    >
                      <MenuItem value="all">All Outcomes</MenuItem>
                      <MenuItem value="answered">Answered</MenuItem>
                      <MenuItem value="no_answer">No Answer</MenuItem>
                      <MenuItem value="failed">Failed</MenuItem>
                    </Select>
                  </FormControl>
                </MDBox>

                {/* Main Table Content */}
                <MDBox pt={1} px={2} pb={3}>
                  {loading ? (
                    <MDBox display="flex" justifyContent="center" alignItems="center" py={8}>
                      <CircularProgress color="info" />
                    </MDBox>
                  ) : error ? (
                    <MDBox display="flex" flexDirection="column" alignItems="center" py={6}>
                      <Icon color="error" sx={{ fontSize: "36px !important", mb: 1 }}>
                        error_outline
                      </Icon>
                      <MDTypography variant="body2" color="text" mb={2}>
                        {error}
                      </MDTypography>
                      <MDButton variant="gradient" color="info" size="small" onClick={fetchLogs}>
                        Retry
                      </MDButton>
                    </MDBox>
                  ) : logs.length === 0 ? (
                    <MDBox display="flex" flexDirection="column" alignItems="center" py={6}>
                      <Icon sx={{ fontSize: "36px !important", color: "grey.400", mb: 1 }}>
                        record_voice_over
                      </Icon>
                      <MDTypography variant="body2" color="text">
                        No voice campaign call logs found.
                      </MDTypography>
                    </MDBox>
                  ) : (
                    <>
                      <TableContainer sx={{ overflowX: "auto" }}>
                        <Table size="small">
                          <TableHead sx={{ display: "table-header-group" }}>
                            <TableRow>
                              <TableCell sx={{ fontWeight: "bold" }}>Customer Phone</TableCell>
                              <TableCell sx={{ fontWeight: "bold" }}>Agent</TableCell>
                              <TableCell sx={{ fontWeight: "bold" }}>Amount</TableCell>
                              <TableCell sx={{ fontWeight: "bold" }}>Timestamp</TableCell>
                              <TableCell sx={{ fontWeight: "bold" }}>Attempts</TableCell>
                              <TableCell sx={{ fontWeight: "bold" }}>Outcome</TableCell>
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
                                <TableCell>
                                  <MDTypography variant="caption" color="text" fontWeight="medium">
                                    {log.agent_id}
                                  </MDTypography>
                                </TableCell>
                                <TableCell>
                                  <MDTypography variant="caption" color="text" fontWeight="medium">
                                    GHS{" "}
                                    {typeof log.amount === "number"
                                      ? log.amount.toFixed(2)
                                      : log.amount}
                                  </MDTypography>
                                </TableCell>
                                <TableCell>
                                  <MDTypography variant="caption" color="text" fontWeight="medium">
                                    {formatTimestamp(log.timestamp)}
                                  </MDTypography>
                                </TableCell>
                                <TableCell>
                                  <MDTypography variant="caption" color="text" fontWeight="medium">
                                    {log.attempt_number || 1}
                                  </MDTypography>
                                </TableCell>
                                <TableCell>{getOutcomeBadge(log.outcome)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>

                      {/* Pagination Controls */}
                      <MDBox
                        display="flex"
                        justifyContent="space-between"
                        alignItems="center"
                        pt={3}
                        px={2}
                      >
                        <MDTypography variant="caption" color="text">
                          Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of{" "}
                          {total} call logs
                        </MDTypography>
                        <MDBox display="flex" gap={1}>
                          <MDButton
                            variant="outlined"
                            color="info"
                            size="small"
                            disabled={page === 0}
                            onClick={() => setPage((prev) => Math.max(prev - 1, 0))}
                          >
                            Previous
                          </MDButton>
                          <MDTypography
                            variant="caption"
                            color="text"
                            sx={{ display: "flex", alignItems: "center", px: 1 }}
                          >
                            Page {page + 1} of {totalPages}
                          </MDTypography>
                          <MDButton
                            variant="outlined"
                            color="info"
                            size="small"
                            disabled={page >= totalPages - 1}
                            onClick={() => setPage((prev) => prev + 1)}
                          >
                            Next
                          </MDButton>
                        </MDBox>
                      </MDBox>
                    </>
                  )}
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

export default VoiceCampaigns;
