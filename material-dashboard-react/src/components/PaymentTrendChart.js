import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import axios from "axios";

// @mui material components
import Card from "@mui/material/Card";
import CircularProgress from "@mui/material/CircularProgress";
import Icon from "@mui/material/Icon";

// Recharts components
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDButton from "components/MDButton";

function PaymentTrendChart({ agentId }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [meanAmount, setMeanAmount] = useState(0);
  const [triggering, setTriggering] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const fetchData = async () => {
    if (!agentId) return;
    setLoading(true);
    setError(null);
    try {
      const apiBase = process.env.REACT_APP_API_BASE || "http://localhost:8000";
      const response = await axios.get(`${apiBase}/api/agents/${agentId}/trend`);
      const trendData = response.data;

      setData(trendData);

      // Compute agent mean amount
      if (trendData.length > 0) {
        const total = trendData.reduce((sum, item) => sum + item.amount, 0);
        const mean = total / trendData.length;
        setMeanAmount(parseFloat(mean.toFixed(2)));
      } else {
        setMeanAmount(0);
      }
    } catch (err) {
      console.error(err);
      setData([]);
      setMeanAmount(0);
      if (err.response) {
        if (err.response.status === 404) {
          setError(`Agent ${agentId} not found in the system.`);
        } else {
          setError(
            `API Error (${err.response.status}): ${
              err.response.data?.detail || "Server error occurred."
            }`
          );
        }
      } else if (err.request) {
        setError("Network error: Could not reach the API server.");
      } else {
        setError(`Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerVoiceCall = async () => {
    if (!agentId || triggering) return;
    setTriggering(true);
    setFeedback(null);
    try {
      const apiBase = process.env.REACT_APP_API_BASE || "http://localhost:8000";
      const token = localStorage.getItem("mifds_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const res = await axios.post(
        `${apiBase}/api/voice/trigger`,
        { agent_id: agentId },
        { headers }
      );

      const msg =
        res.data?.message ||
        `Call triggered successfully. Outcome: ${res.data?.data?.outcome || "completed"}`;
      setFeedback({ type: "success", message: msg });
    } catch (err) {
      console.error(err);
      const errDetail = err.response?.data?.detail || err.message || "Failed to trigger call";
      setFeedback({ type: "error", message: `Call failed: ${errDetail}` });
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [agentId]);

  // Formatter for timestamp dates
  const formatXAxis = (tickItem) => {
    try {
      if (!tickItem) return "";
      const date = new Date(tickItem);
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch (e) {
      return tickItem;
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      const formattedDate = new Date(dataPoint.timestamp).toLocaleString();
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
          <MDTypography variant="caption" color="text" display="block">
            Timestamp: <strong>{formattedDate}</strong>
          </MDTypography>
          <MDTypography variant="caption" color="text" display="block">
            Amount: <strong>GHS {dataPoint.amount.toFixed(2)}</strong>
          </MDTypography>
          <MDTypography variant="caption" color="text" display="block">
            Method: <strong>{dataPoint.payment_method}</strong>
          </MDTypography>
          <MDTypography variant="caption" color="text" display="block">
            Remittance: <strong>{dataPoint.remittance_status}</strong>
          </MDTypography>
          <MDTypography
            variant="caption"
            color={dataPoint.is_fraud ? "error" : "success"}
            fontWeight="bold"
            display="block"
          >
            Risk: {dataPoint.risk_score.toFixed(1)}% {dataPoint.is_fraud ? "(Flagged)" : ""}
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
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mx={2}
        mt={-3}
        py={2}
        px={2}
        variant="gradient"
        bgColor="success"
        borderRadius="lg"
        coloredShadow="success"
      >
        <MDBox>
          <MDTypography variant="h6" color="white">
            Premium Payment Trend: {agentId}
          </MDTypography>
          <MDTypography variant="caption" color="white" display="block">
            Transaction history and mean threshold analysis
          </MDTypography>
        </MDBox>
        <MDButton
          variant="gradient"
          color="white"
          size="small"
          disabled={triggering || loading}
          onClick={handleTriggerVoiceCall}
          sx={{ ml: 2, whitespace: "nowrap" }}
        >
          {triggering ? (
            <MDBox display="flex" alignItems="center">
              <CircularProgress size={16} color="inherit" sx={{ mr: 1 }} />
              Calling...
            </MDBox>
          ) : (
            <MDBox display="flex" alignItems="center">
              <Icon sx={{ mr: 0.5 }}>phone_in_talk</Icon>
              Call Customer
            </MDBox>
          )}
        </MDButton>
      </MDBox>

      {feedback && (
        <MDBox
          mx={2}
          mt={2}
          px={2}
          py={1}
          borderRadius="md"
          bgColor={feedback.type === "success" ? "success" : "error"}
        >
          <MDTypography variant="caption" color="white" fontWeight="bold">
            {feedback.message}
          </MDTypography>
        </MDBox>
      )}

      <MDBox
        pt={3}
        px={2}
        pb={2}
        flexGrow={1}
        display="flex"
        flexDirection="column"
        justifyContent="center"
      >
        {loading ? (
          <MDBox display="flex" justifyContent="center" alignItems="center" height="240px">
            <CircularProgress color="success" />
          </MDBox>
        ) : error ? (
          <MDBox
            display="flex"
            flexDirection="column"
            justifyContent="center"
            alignItems="center"
            height="240px"
            px={2}
          >
            <Icon color="error" sx={{ fontSize: "36px !important", mb: 1 }}>
              error_outline
            </Icon>
            <MDTypography variant="caption" color="text" align="center" mb={2}>
              {error}
            </MDTypography>
            <MDButton variant="gradient" color="success" size="small" onClick={fetchData}>
              Retry
            </MDButton>
          </MDBox>
        ) : data.length === 0 ? (
          <MDBox
            display="flex"
            flexDirection="column"
            justifyContent="center"
            alignItems="center"
            height="240px"
          >
            <Icon sx={{ fontSize: "36px !important", color: "grey.400", mb: 1 }}>history</Icon>
            <MDTypography variant="caption" color="text">
              No transaction history available in the last 30 days.
            </MDTypography>
          </MDBox>
        ) : (
          <MDBox height="240px" width="100%">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatXAxis}
                  stroke="#7b809a"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#7b809a"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  unit=" GHS"
                />
                <Tooltip content={<CustomTooltip />} />

                {/* Reference line for the agent's mean transaction amount */}
                <ReferenceLine
                  y={meanAmount}
                  stroke="#43a047"
                  strokeDasharray="4 4"
                  label={{
                    value: `Mean GHS ${meanAmount}`,
                    fill: "#2e7d32",
                    fontSize: 10,
                    position: "top",
                  }}
                />

                <Line
                  type="monotone"
                  dataKey="amount"
                  stroke="#4caf50"
                  strokeWidth={2.5}
                  dot={{ r: 4, stroke: "#4caf50", strokeWidth: 1.5, fill: "#fff" }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </MDBox>
        )}
      </MDBox>
    </Card>
  );
}

PaymentTrendChart.propTypes = {
  agentId: PropTypes.string.isRequired,
};

export default PaymentTrendChart;
