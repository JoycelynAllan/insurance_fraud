import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
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
import InputAdornment from "@mui/material/InputAdornment";
import Icon from "@mui/material/Icon";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDBadge from "components/MDBadge";
import MDButton from "components/MDButton";

import { getApiBase } from "utils/apiConfig";

function AgentRiskTable({ selectedAgentId, onSelectAgent, branchFilter, onClearBranchFilter }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [actionMessage, setActionMessage] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const response = await axios.get(`${apiBase}/api/agents/risk`, { headers });

      // Sort descending by risk score
      const sorted = (Array.isArray(response.data) ? response.data : []).sort(
        (a, b) => (b.risk_score || 0) - (a.risk_score || 0)
      );
      setData(sorted);
    } catch (err) {
      console.error("[API Error - AgentRiskTable]", err);
      setError("Failed to fetch risk data from API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSearchChange = (event) => {
    setSearch(event.target.value);
  };

  const handleInvestigate = async (agentId, alertId = 1) => {
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      await axios.post(
        `${apiBase}/api/alerts/${alertId}/acknowledge`,
        { status: "INVESTIGATING" },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setActionMessage(`Investigation opened for Agent ${agentId}`);
      setTimeout(() => setActionMessage(""), 4000);
      fetchData();
    } catch (err) {
      console.error("Failed to set status to INVESTIGATING:", err);
    }
  };

  const handleCallCustomer = async (agentRow) => {
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      await axios.post(
        `${apiBase}/api/voice/trigger`,
        {
          customer_phone: agentRow.customer_phone || "+233200000000",
          agent_id: agentRow.agent_id,
          amount: agentRow.amount || 150.0,
          language: agentRow.language_pref || "english",
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setActionMessage(`Outbound reminder call dispatched for Agent ${agentRow.agent_id}`);
      setTimeout(() => setActionMessage(""), 4000);
    } catch (err) {
      console.error("Failed to trigger outbound voice reminder:", err);
    }
  };

  const getRiskColor = (score) => {
    const val = score <= 1.0 ? score * 100 : score;
    if (val < 40) return "success";
    if (val < 70) return "warning";
    return "error";
  };

  // Filter agents based on search term and branchFilter
  const filteredData = data.filter((item) => {
    const term = search.toLowerCase();
    const matchesSearch =
      !term ||
      (item.agent_id && item.agent_id.toLowerCase().includes(term)) ||
      (item.branch && item.branch.toLowerCase().includes(term));
    const matchesBranch =
      !branchFilter || (item.branch && item.branch.toLowerCase() === branchFilter.toLowerCase());
    return matchesSearch && matchesBranch;
  });

  return (
    <Card sx={{ height: "100%", minHeight: "380px" }}>
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
        <MDBox display="flex" alignItems="center" gap={1}>
          <MDTypography variant="h6" color="white">
            Agent Risk Profiles {branchFilter ? `(${branchFilter})` : ""}
          </MDTypography>
          {branchFilter && (
            <MDButton
              variant="outlined"
              color="white"
              size="small"
              onClick={onClearBranchFilter}
              sx={{ py: 0.2, px: 1, fontSize: "0.7rem" }}
            >
              Clear Filter
            </MDButton>
          )}
        </MDBox>
        <TextField
          size="small"
          placeholder="Filter by ID or Branch..."
          value={search}
          onChange={handleSearchChange}
          sx={{
            backgroundColor: "rgba(255, 255, 255, 0.9)",
            borderRadius: "4px",
            width: "220px",
            "& .MuiOutlinedInput-root": {
              "& fieldset": { borderColor: "transparent" },
            },
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Icon>search</Icon>
              </InputAdornment>
            ),
          }}
        />
      </MDBox>

      {actionMessage && (
        <MDBox px={2} pt={2} textAlign="center">
          <MDTypography variant="caption" color="success" fontWeight="bold">
            {actionMessage}
          </MDTypography>
        </MDBox>
      )}

      <MDBox pt={2} px={2} pb={2} flexGrow={1} display="flex" flexDirection="column">
        {loading ? (
          <MDBox display="flex" justifyContent="center" alignItems="center" flexGrow={1} py={8}>
            <CircularProgress color="info" />
          </MDBox>
        ) : error ? (
          <MDBox display="flex" flexDirection="column" alignItems="center" py={6}>
            <MDTypography variant="body2" color="text" mb={2}>
              {error}
            </MDTypography>
            <MDButton variant="gradient" color="info" size="small" onClick={fetchData}>
              Retry
            </MDButton>
          </MDBox>
        ) : (
          <TableContainer sx={{ maxHeight: "360px", overflowY: "auto", overflowX: "auto" }}>
            <Table
              stickyHeader
              size="small"
              sx={{ tableLayout: "fixed", width: "100%", minWidth: "750px" }}
            >
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold", width: "16%" }}>Agent ID</TableCell>
                  <TableCell sx={{ fontWeight: "bold", width: "16%" }}>Branch</TableCell>
                  <TableCell sx={{ fontWeight: "bold", width: "15%" }} align="center">
                    Risk Score
                  </TableCell>
                  <TableCell sx={{ fontWeight: "bold", width: "14%" }} align="center">
                    Status
                  </TableCell>
                  <TableCell sx={{ fontWeight: "bold", width: "15%" }} align="right">
                    Amount
                  </TableCell>
                  <TableCell sx={{ fontWeight: "bold", width: "24%" }} align="center">
                    Actions
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredData.map((row, idx) => {
                  const agentId = row.agent_id || `AGT-${idx + 1}`;
                  const isSelected = selectedAgentId === agentId;
                  const numericScore =
                    typeof row.risk_score === "number"
                      ? row.risk_score
                      : parseFloat(row.risk_score) || 0.0;
                  const scorePct = numericScore <= 1.0 ? numericScore * 100 : numericScore;
                  const isDisabled = scorePct < 40.0;

                  return (
                    <TableRow
                      key={agentId}
                      hover
                      onClick={() => onSelectAgent(agentId)}
                      selected={isSelected}
                      sx={{
                        cursor: "pointer",
                        backgroundColor: isSelected
                          ? "rgba(0, 180, 216, 0.15) !important"
                          : "inherit",
                      }}
                    >
                      <TableCell align="left">
                        <MDTypography variant="button" fontWeight="medium">
                          {agentId}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="left">
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          {row.branch || "Accra"}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="center">
                        <MDBadge
                          badgeContent={`${scorePct.toFixed(1)}%`}
                          color={getRiskColor(scorePct)}
                          variant="gradient"
                          size="xs"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          {row.status || "pending"}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="right">
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          GHS {(row.amount || 0).toFixed(2)}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="center" onClick={(e) => e.stopPropagation()}>
                        <MDBox display="flex" gap={0.5} justifyContent="center">
                          <MDButton
                            variant="gradient"
                            color="warning"
                            size="small"
                            disabled={isDisabled}
                            onClick={() => handleInvestigate(agentId, row.id || 1)}
                            sx={{ py: 0.3, px: 1, fontSize: "0.65rem" }}
                          >
                            Investigate
                          </MDButton>
                          <MDButton
                            variant="gradient"
                            color="info"
                            size="small"
                            disabled={isDisabled}
                            onClick={() => handleCallCustomer(row)}
                            sx={{ py: 0.3, px: 1, fontSize: "0.65rem" }}
                          >
                            Call Customer
                          </MDButton>
                        </MDBox>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </MDBox>
    </Card>
  );
}

AgentRiskTable.propTypes = {
  selectedAgentId: PropTypes.string.isRequired,
  onSelectAgent: PropTypes.func.isRequired,
  branchFilter: PropTypes.string,
  onClearBranchFilter: PropTypes.func,
};

AgentRiskTable.defaultProps = {
  branchFilter: "",
  onClearBranchFilter: () => {},
};

export default AgentRiskTable;
