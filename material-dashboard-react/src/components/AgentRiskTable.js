import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import axios from "axios";
import toast from "react-hot-toast";

// @mui material components
import Card from "@mui/material/Card";
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

const thStyle = {
  padding: "12px 8px",
  textAlign: "left",
  fontWeight: "bold",
  fontSize: "13px",
  color: "#344767",
  borderBottom: "2px solid #dee2e6",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const tdStyle = {
  padding: "12px 8px",
  textAlign: "left",
  fontSize: "13px",
  color: "#495057",
  borderBottom: "1px solid #f0f0f0",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  verticalAlign: "middle",
};

const trStyle = {
  cursor: "pointer",
  transition: "background-color 0.15s",
};

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
    <Card sx={{ height: "100%", minHeight: "380px", overflow: "hidden", width: "100%" }}>
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
          <MDBox sx={{ width: "100%", overflowX: "hidden", maxHeight: "360px", overflowY: "auto" }}>
            <table
              style={{
                width: "100%",
                tableLayout: "fixed",
                borderCollapse: "collapse",
                fontSize: "13px",
              }}
            >
              <colgroup>
                <col style={{ width: "15%" }} />
                <col style={{ width: "18%" }} />
                <col style={{ width: "14%" }} />
                <col style={{ width: "14%" }} />
                <col style={{ width: "19%" }} />
                <col style={{ width: "20%" }} />
              </colgroup>
              <thead>
                <tr style={{ backgroundColor: "#f8f9fa" }}>
                  <th style={thStyle}>Agent ID</th>
                  <th style={thStyle}>Branch</th>
                  <th style={thStyle}>Risk Score</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Amount</th>
                  <th style={thStyle}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((agent) => {
                  const agentId = agent.agent_id;
                  const isSelected = selectedAgentId === agentId;
                  const numericScore =
                    typeof agent.risk_score === "number"
                      ? agent.risk_score
                      : parseFloat(agent.risk_score) || 0.0;
                  const scorePct = numericScore <= 1.0 ? numericScore * 100 : numericScore;
                  const isBelowThreshold = scorePct < 40.0;

                  return (
                    <tr
                      key={agentId}
                      style={{
                        ...trStyle,
                        backgroundColor: isSelected ? "rgba(0, 180, 216, 0.15)" : "transparent",
                      }}
                      onClick={() => onSelectAgent(agentId)}
                    >
                      <td style={tdStyle}>
                        <strong>{agentId}</strong>
                      </td>
                      <td style={tdStyle}>{agent.branch || "Accra"}</td>
                      <td style={{ ...tdStyle, textAlign: "center" }}>
                        <MDBadge
                          badgeContent={`${scorePct.toFixed(1)}%`}
                          color={getRiskColor(scorePct)}
                          variant="gradient"
                          size="xs"
                        />
                      </td>
                      <td style={{ ...tdStyle, textTransform: "capitalize" }}>
                        {agent.status || "pending"}
                      </td>
                      <td style={tdStyle}>GHS {(agent.amount || 0).toFixed(2)}</td>
                      <td style={{ ...tdStyle, textAlign: "center" }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCallCustomer(agent);
                          }}
                          disabled={isBelowThreshold}
                          title={
                            isBelowThreshold
                              ? "Risk score below threshold"
                              : "Call this agent's customer"
                          }
                          style={{
                            backgroundColor: isBelowThreshold ? "#9e9e9e" : "#212121",
                            color: "white",
                            border: "none",
                            borderRadius: "6px",
                            padding: "6px 10px",
                            fontSize: "11px",
                            fontWeight: "bold",
                            cursor: isBelowThreshold ? "not-allowed" : "pointer",
                            whiteSpace: "nowrap",
                            width: "100%",
                            maxWidth: "120px",
                          }}
                        >
                          CALL CUSTOMER
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </MDBox>
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
