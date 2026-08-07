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

function AgentRiskTable({ selectedAgentId, onSelectAgent }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = getApiBase();
      const response = await axios.get(`${apiBase}/api/agents/risk`);
      setData(response.data);
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

  const getRiskColor = (score) => {
    if (score < 40) return "success";
    if (score < 70) return "warning";
    return "error";
  };

  // Filter agents based on agent_id or branch
  const filteredData = data.filter((item) => {
    const term = search.toLowerCase();
    const matchesAgent = item.agent_id ? item.agent_id.toLowerCase().includes(term) : false;
    const matchesBranch = item.branch ? item.branch.toLowerCase().includes(term) : false;
    return matchesAgent || matchesBranch;
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
        <MDTypography variant="h6" color="white">
          Agent Risk Profiles
        </MDTypography>
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
              "&:hover fieldset": { borderColor: "transparent" },
              "&.Mui-focused fieldset": { borderColor: "transparent" },
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

      <MDBox pt={3} px={2} pb={2} flexGrow={1} display="flex" flexDirection="column">
        {loading ? (
          <MDBox display="flex" justifyContent="center" alignItems="center" flexGrow={1} py={8}>
            <CircularProgress color="info" />
          </MDBox>
        ) : error ? (
          <MDBox
            display="flex"
            flexDirection="column"
            justifyContent="center"
            alignItems="center"
            flexGrow={1}
            py={6}
          >
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
              sx={{ tableLayout: "fixed", width: "100%", minWidth: "650px" }}
            >
              <TableHead>
                <TableRow>
                  <TableCell
                    sx={{ fontWeight: "bold", width: "20%", minWidth: "110px" }}
                    align="left"
                  >
                    Agent ID
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", width: "20%", minWidth: "110px" }}
                    align="left"
                  >
                    Branch
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", width: "18%", minWidth: "100px" }}
                    align="center"
                  >
                    Risk Score
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", width: "14%", minWidth: "90px" }}
                    align="center"
                  >
                    Status
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", width: "16%", minWidth: "100px" }}
                    align="right"
                  >
                    Amount
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", width: "12%", minWidth: "90px" }}
                    align="center"
                  >
                    Date
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredData.map((row, idx) => {
                  const agentId = row.agent_id || row.agentId || `AGT-${idx + 1}`;
                  const isSelected = selectedAgentId === agentId;

                  const rawScore =
                    row.risk_score !== undefined && row.risk_score !== null
                      ? row.risk_score
                      : row.riskScore;
                  const numericScore =
                    typeof rawScore === "number" ? rawScore : parseFloat(rawScore) || 0.0;
                  const riskColor = getRiskColor(numericScore);

                  const rawAmount =
                    row.amount !== undefined && row.amount !== null ? row.amount : row.total_amount;
                  const numericAmount =
                    typeof rawAmount === "number" ? rawAmount : parseFloat(rawAmount) || 0.0;

                  const statusText =
                    row.status || row.remittance_status || (row.is_fraud ? "FLAGGED" : "CLEARED");
                  const dateRaw = row.date || row.timestamp || row.created_at;
                  const dateText = dateRaw ? String(dateRaw).split(" ")[0].split("T")[0] : "-";

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
                        "&:hover": {
                          backgroundColor: "rgba(0, 0, 0, 0.04) !important",
                        },
                      }}
                    >
                      <TableCell align="left" sx={{ width: "20%", minWidth: "110px" }}>
                        <MDTypography variant="button" fontWeight="medium">
                          {agentId}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="left" sx={{ width: "20%", minWidth: "110px" }}>
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          {row.branch || "General"}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="center" sx={{ width: "18%", minWidth: "100px" }}>
                        <MDBadge
                          badgeContent={`${numericScore.toFixed(1)}%`}
                          color={riskColor}
                          variant="gradient"
                          size="xs"
                        />
                      </TableCell>
                      <TableCell align="center" sx={{ width: "14%", minWidth: "90px" }}>
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          {statusText}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="right" sx={{ width: "16%", minWidth: "100px" }}>
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          GHS {numericAmount.toFixed(2)}
                        </MDTypography>
                      </TableCell>
                      <TableCell align="center" sx={{ width: "12%", minWidth: "90px" }}>
                        <MDTypography variant="caption" color="text" fontWeight="medium">
                          {dateText}
                        </MDTypography>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {filteredData.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <MDTypography variant="caption" color="text" py={3}>
                        No records match the filter.
                      </MDTypography>
                    </TableCell>
                  </TableRow>
                )}
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
};

export default AgentRiskTable;
