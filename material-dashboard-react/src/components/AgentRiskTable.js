import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import axios from "axios";
import toast from "react-hot-toast";

// @mui material components
import Card from "@mui/material/Card";
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
import Tooltip from "@mui/material/Tooltip";

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

  const handleCallCustomer = async (agentRow) => {
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      const lang = agentRow.language_pref || "english";

      await axios.post(
        `${apiBase}/api/voice/trigger`,
        {
          customer_phone: agentRow.customer_phone || "+233200000000",
          agent_id: agentRow.agent_id,
          amount: agentRow.amount || 150.0,
          language: lang,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`SMS reminder scheduled for customer of ${agentRow.agent_id} in ${lang}`);
    } catch (err) {
      console.error("Failed to trigger outbound voice reminder:", err);
      toast.error("Failed to schedule call. Please try again.");
    }
  };

  const getRiskColor = (score) => {
    const val = score <= 1.0 ? score * 100 : score;
    if (val < 40) return "success";
    if (val < 70) return "warning";
    return "error";
  };

  const getStatusTextColor = (statusStr) => {
    const s = (statusStr || "").toLowerCase();
    if (s === "missed") return "error";
    if (s === "pending") return "warning";
    if (s === "remitted") return "success";
    return "text";
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

  // Common cell style for truncation and fixed width enforcement
  const commonCellStyle = {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    textAlign: "center",
    verticalAlign: "middle",
    px: 1,
  };

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
          <TableContainer sx={{ maxHeight: "360px", overflowY: "auto", overflowX: "hidden" }}>
            <Table stickyHeader size="small" sx={{ tableLayout: "fixed", width: "100%" }}>
              <TableHead>
                <TableRow sx={{ height: "48px" }}>
                  <TableCell sx={{ ...commonCellStyle, width: "120px", fontWeight: "bold" }}>
                    Agent ID
                  </TableCell>
                  <TableCell sx={{ ...commonCellStyle, width: "120px", fontWeight: "bold" }}>
                    Branch
                  </TableCell>
                  <TableCell sx={{ ...commonCellStyle, width: "100px", fontWeight: "bold" }}>
                    Risk Score
                  </TableCell>
                  <TableCell sx={{ ...commonCellStyle, width: "100px", fontWeight: "bold" }}>
                    Status
                  </TableCell>
                  <TableCell sx={{ ...commonCellStyle, width: "130px", fontWeight: "bold" }}>
                    Amount
                  </TableCell>
                  <TableCell sx={{ ...commonCellStyle, width: "150px", fontWeight: "bold" }}>
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
                  const isBelowThreshold = scorePct < 40.0;

                  return (
                    <TableRow
                      key={agentId}
                      hover
                      onClick={() => onSelectAgent(agentId)}
                      selected={isSelected}
                      sx={{
                        height: "56px",
                        verticalAlign: "middle",
                        cursor: "pointer",
                        backgroundColor: isSelected
                          ? "rgba(0, 180, 216, 0.15) !important"
                          : "inherit",
                      }}
                    >
                      <TableCell sx={{ ...commonCellStyle, width: "120px" }}>
                        <MDTypography variant="button" fontWeight="medium">
                          {agentId}
                        </MDTypography>
                      </TableCell>
                      <TableCell sx={{ ...commonCellStyle, width: "120px" }}>
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          {row.branch || "Accra"}
                        </MDTypography>
                      </TableCell>
                      <TableCell sx={{ ...commonCellStyle, width: "100px" }}>
                        <MDBox display="flex" justifyContent="center" alignItems="center">
                          <MDBadge
                            badgeContent={`${scorePct.toFixed(1)}%`}
                            color={getRiskColor(scorePct)}
                            variant="gradient"
                            size="xs"
                          />
                        </MDBox>
                      </TableCell>
                      <TableCell sx={{ ...commonCellStyle, width: "100px" }}>
                        <MDTypography
                          variant="caption"
                          color={getStatusTextColor(row.status)}
                          fontWeight="bold"
                          sx={{ textTransform: "capitalize" }}
                        >
                          {row.status || "pending"}
                        </MDTypography>
                      </TableCell>
                      <TableCell sx={{ ...commonCellStyle, width: "130px" }}>
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          GHS {(row.amount || 0).toFixed(2)}
                        </MDTypography>
                      </TableCell>
                      <TableCell
                        sx={{ ...commonCellStyle, width: "150px" }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MDBox display="flex" justifyContent="center" alignItems="center">
                          {isBelowThreshold ? (
                            <Tooltip title="Risk score below threshold — no action needed" arrow>
                              <span
                                style={{
                                  width: "100%",
                                  maxWidth: "130px",
                                  display: "inline-block",
                                }}
                              >
                                <MDButton
                                  variant="gradient"
                                  color="secondary"
                                  size="small"
                                  disabled
                                  fullWidth
                                  sx={{
                                    py: "6px",
                                    px: "8px",
                                    fontSize: "11px",
                                    whiteSpace: "nowrap",
                                    lineHeight: 1.2,
                                  }}
                                >
                                  CALL CUSTOMER
                                </MDButton>
                              </span>
                            </Tooltip>
                          ) : (
                            <MDButton
                              variant="gradient"
                              color="dark"
                              size="small"
                              fullWidth
                              onClick={() => handleCallCustomer(row)}
                              sx={{
                                py: "6px",
                                px: "8px",
                                fontSize: "11px",
                                whiteSpace: "nowrap",
                                lineHeight: 1.2,
                                maxWidth: "130px",
                              }}
                            >
                              CALL CUSTOMER
                            </MDButton>
                          )}
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
