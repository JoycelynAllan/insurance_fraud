import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import axios from "axios";

// @mui material components
import Card from "@mui/material/Card";
import CircularProgress from "@mui/material/CircularProgress";

// Recharts components
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDButton from "components/MDButton";

import { getApiBase } from "utils/apiConfig";

function BranchHeatmap({ onSelectBranch }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const response = await axios.get(`${apiBase}/api/agents/risk`, { headers });

      const branchGroups = {};
      (Array.isArray(response.data) ? response.data : []).forEach((agent) => {
        const branch = agent.branch || "Accra";
        const score = typeof agent.risk_score === "number" ? agent.risk_score : parseFloat(agent.risk_score) || 0;
        const scorePct = score <= 1.0 ? score * 100 : score;
        const isFlagged = scorePct >= 70.0 || agent.is_fraud;

        if (!branchGroups[branch]) {
          branchGroups[branch] = { sum: 0, count: 0, flaggedCount: 0, maxRisk: 0 };
        }
        branchGroups[branch].sum += scorePct;
        branchGroups[branch].count += 1;
        if (isFlagged) branchGroups[branch].flaggedCount += 1;
        if (scorePct > branchGroups[branch].maxRisk) {
          branchGroups[branch].maxRisk = scorePct;
        }
      });

      const formattedData = Object.keys(branchGroups).map((branch) => ({
        branch,
        avgRisk: parseFloat((branchGroups[branch].sum / branchGroups[branch].count).toFixed(1)),
        agentCount: branchGroups[branch].count,
        flaggedCount: branchGroups[branch].flaggedCount,
        maxRisk: parseFloat(branchGroups[branch].maxRisk.toFixed(1)),
      }));

      formattedData.sort((a, b) => a.branch.localeCompare(b.branch));
      setData(formattedData);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch branch heatmap details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <MDBox
          p={1.5}
          bgColor="white"
          borderRadius="md"
          sx={{
            boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)",
            border: "1px solid #e0e0e0",
          }}
        >
          <MDTypography variant="button" fontWeight="bold" display="block" mb={0.5} color="dark">
            {dataPoint.branch} Branch
          </MDTypography>
          <MDTypography variant="caption" color="text" display="block">
            Flagged Agents: <strong>{dataPoint.flaggedCount}</strong>
          </MDTypography>
          <MDTypography variant="caption" color="text" display="block">
            Highest Risk Score: <strong style={{ color: "#d32f2f" }}>{dataPoint.maxRisk}%</strong>
          </MDTypography>
          <MDTypography variant="caption" color="text" display="block">
            Avg Risk Score: <strong>{dataPoint.avgRisk}%</strong>
          </MDTypography>
        </MDBox>
      );
    }
    return null;
  };

  CustomTooltip.propTypes = {
    active: PropTypes.bool,
    payload: PropTypes.arrayOf(PropTypes.object),
  };

  return (
    <Card sx={{ height: "100%", minHeight: "360px" }}>
      <MDBox
        mx={2}
        mt={-3}
        py={2}
        px={2}
        variant="gradient"
        bgColor="warning"
        borderRadius="lg"
        coloredShadow="warning"
      >
        <MDTypography variant="h6" color="white">
          Branch Risk Distribution (Click Bar to Filter)
        </MDTypography>
      </MDBox>

      <MDBox pt={3} px={2} pb={2} flexGrow={1} display="flex" flexDirection="column" justifyContent="center">
        {loading ? (
          <MDBox display="flex" justifyContent="center" alignItems="center" height="240px">
            <CircularProgress color="warning" />
          </MDBox>
        ) : error ? (
          <MDBox display="flex" flexDirection="column" justifyContent="center" alignItems="center" height="240px">
            <MDTypography variant="body2" color="text" mb={2}>
              {error}
            </MDTypography>
            <MDButton variant="gradient" color="warning" size="small" onClick={fetchData}>
              Retry
            </MDButton>
          </MDBox>
        ) : (
          <MDBox height="240px" width="100%">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
                <XAxis dataKey="branch" stroke="#7b809a" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#7b809a" fontSize={12} tickLine={false} axisLine={false} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="avgRisk"
                  fill="#f44336"
                  radius={[4, 4, 0, 0]}
                  barSize={40}
                  onClick={(entry) => {
                    if (entry && entry.branch && onSelectBranch) {
                      onSelectBranch(entry.branch);
                    }
                  }}
                  style={{ cursor: "pointer" }}
                >
                  {data.map((entry, index) => {
                    let barColor = "#ef5350";
                    if (entry.maxRisk >= 70) barColor = "#d32f2f";
                    else if (entry.avgRisk < 40) barColor = "#4caf50";
                    return <Cell key={`cell-${index}`} fill={barColor} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </MDBox>
        )}
      </MDBox>
    </Card>
  );
}

BranchHeatmap.propTypes = {
  onSelectBranch: PropTypes.func,
};

BranchHeatmap.defaultProps = {
  onSelectBranch: () => {},
};

export default BranchHeatmap;
