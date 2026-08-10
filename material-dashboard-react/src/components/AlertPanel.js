import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import toast from "react-hot-toast";

// @mui material components
import Card from "@mui/material/Card";
import Icon from "@mui/material/Icon";
import Divider from "@mui/material/Divider";
import CircularProgress from "@mui/material/CircularProgress";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDBadge from "components/MDBadge";
import MDButton from "components/MDButton";

import { getApiBase, getWsBase } from "utils/apiConfig";

function AlertPanel() {
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState("Connecting"); // Connecting, Connected, Disconnected
  const socketRef = useRef(null);

  useEffect(() => {
    let reconnectTimeout = null;
    let delay = 3000; // start with 3s backoff

    const connectWebSocket = () => {
      setStatus("Connecting");
      const token = localStorage.getItem("mifds_token") || "";
      if (!token) {
        setStatus("Disconnected");
        return;
      }

      const wsBase = getWsBase();
      const socket = new WebSocket(`${wsBase}/api/alerts?token=${encodeURIComponent(token)}`);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log("WebSocket connection established");
        setStatus("Connected");
        delay = 3000; // reset backoff on successful connection
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Filter out ping and error messages
          if (!data || data.type === "ping" || data.type === "error") {
            return;
          }

          if (data.type === "alert" || !data.type) {
            setAlerts((prevAlerts) => {
              const filtered = prevAlerts.filter(
                (a) =>
                  data.id &&
                  String(a.id) !== String(data.id) &&
                  data.agent_id &&
                  String(a.agent_id) !== String(data.agent_id)
              );
              const updated = [data, ...filtered];
              updated.sort((a, b) => {
                const scoreA =
                  typeof a.risk_score === "number"
                    ? a.risk_score
                    : parseFloat(a.risk_score) || 0;
                const scoreB =
                  typeof b.risk_score === "number"
                    ? b.risk_score
                    : parseFloat(b.risk_score) || 0;
                return scoreB - scoreA;
              });
              return updated;
            });
          } else if (data.type === "update") {
            setAlerts((prevAlerts) =>
              prevAlerts.map((a) =>
                String(a.id) === String(data.id) || String(a.agent_id) === String(data.agent_id)
                  ? { ...a, status: data.status || a.status }
                  : a
              )
            );
          }
        } catch (e) {
          console.error("Error parsing WebSocket message data:", e);
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error observed:", error);
        setStatus("Disconnected");
      };

      socket.onclose = () => {
        console.log(`WebSocket connection closed. Reconnecting in ${delay / 1000}s...`);
        setStatus("Disconnected");
        reconnectTimeout = setTimeout(() => {
          connectWebSocket();
        }, delay);
        delay = Math.min(delay * 1.5, 30000); // exponential backoff capped at 30s
      };
    };

    connectWebSocket();

    // Clean up on unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, []);

  const handleAcknowledge = async (alertId, agentId) => {
    try {
      const apiBase = getApiBase();
      const token = localStorage.getItem("mifds_token");
      await axios.post(
        `${apiBase}/api/alerts/${alertId || 1}/acknowledge`,
        { status: "INVESTIGATING" },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Real-time local state update
      setAlerts((prev) =>
        prev.map((a) =>
          String(a.id) === String(alertId) || String(a.agent_id) === String(agentId)
            ? { ...a, status: "INVESTIGATING" }
            : a
        )
      );
      toast.success("Alert acknowledged");
    } catch (err) {
      console.error("Error acknowledging alert:", err);
      toast.error("Failed to acknowledge alert");
    }
  };

  const getStatusColor = () => {
    if (status === "Connected") return "success";
    if (status === "Connecting") return "warning";
    return "error";
  };

  const getBadgeColor = (statusStr) => {
    switch ((statusStr || "").toUpperCase()) {
      case "RESOLVED":
        return "success";
      case "INVESTIGATING":
        return "warning";
      case "PENDING":
      default:
        return "error";
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    try {
      const dt = new Date(dateStr);
      return dt.toLocaleString();
    } catch (e) {
      return dateStr;
    }
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
        bgColor="dark"
        borderRadius="lg"
        coloredShadow="dark"
      >
        <MDBox display="flex" alignItems="center">
          <Icon sx={{ color: "error.main", mr: 1, animation: "pulse 2s infinite" }}>
            notifications_active
          </Icon>
          <MDTypography variant="h6" color="white">
            Real-Time Fraud Alerts
          </MDTypography>
        </MDBox>
        <MDBox display="flex" alignItems="center">
          {status === "Connecting" && (
            <CircularProgress size={12} color="inherit" sx={{ mr: 1, color: "white" }} />
          )}
          <MDBadge badgeContent={status} color={getStatusColor()} variant="gradient" size="xs" />
        </MDBox>
      </MDBox>

      <MDBox pt={3} px={2} pb={2} flexGrow={1} display="flex" flexDirection="column">
        <MDBox
          flexGrow={1}
          sx={{
            maxHeight: "340px",
            overflowY: "auto",
            pr: 0.5,
          }}
        >
          {status === "Connecting" && alerts.length === 0 ? (
            <MDBox
              display="flex"
              flexDirection="column"
              justifyContent="center"
              alignItems="center"
              height="100%"
              py={8}
            >
              <CircularProgress color="info" size={32} sx={{ mb: 2 }} />
              <MDTypography variant="button" color="text" fontWeight="medium">
                Connecting to live alerts...
              </MDTypography>
            </MDBox>
          ) : alerts.length === 0 ? (
            <MDBox
              display="flex"
              flexDirection="column"
              justifyContent="center"
              alignItems="center"
              height="100%"
              py={8}
            >
              <Icon sx={{ fontSize: "40px !important", color: "grey.400", mb: 1 }}>lock_open</Icon>
              <MDTypography variant="button" color="text" fontWeight="medium">
                No active alerts detected.
              </MDTypography>
              <MDTypography variant="caption" color="text" align="center" mt={0.5}>
                Real-time transaction assessments are active. Alerts will display here.
              </MDTypography>
            </MDBox>
          ) : (
            alerts.map((alert, index) => {
              const numericScore =
                typeof alert.risk_score === "number"
                  ? alert.risk_score
                  : parseFloat(alert.risk_score) || 0;
              const scorePct = numericScore <= 1.0 ? numericScore * 100 : numericScore;
              const formattedScore = alert.risk_score_pct || `${scorePct.toFixed(1)}%`;
              const isHighRisk = scorePct >= 70.0;
              const isPending = (alert.status || "PENDING").toUpperCase() === "PENDING";

              return (
                <MDBox key={alert.id || alert.agent_id || index} mb={2}>
                  <MDBox
                    p={2}
                    borderRadius="lg"
                    sx={{
                      border: "1px solid #f0f0f0",
                      borderLeft:
                        (alert.status || "").toUpperCase() === "PENDING"
                          ? "4px solid #f44336"
                          : (alert.status || "").toUpperCase() === "INVESTIGATING"
                          ? "4px solid #ff9800"
                          : "4px solid #4caf50",
                      backgroundColor: isHighRisk
                        ? "rgba(244, 67, 54, 0.04)"
                        : "rgba(255, 152, 0, 0.04)",
                    }}
                  >
                    <MDBox display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <MDTypography variant="button" fontWeight="bold" color="dark">
                        {alert.agent_id}
                      </MDTypography>
                      <MDBadge
                        badgeContent={alert.status || "PENDING"}
                        color={getBadgeColor(alert.status)}
                        variant="gradient"
                        size="xs"
                      />
                    </MDBox>
                    <MDTypography
                      variant="h4"
                      fontWeight="bold"
                      color="error"
                      sx={{ my: 0.5, fontSize: "22px" }}
                    >
                      {formattedScore}
                    </MDTypography>
                    <MDTypography
                      variant="caption"
                      color="text"
                      fontWeight="medium"
                      display="block"
                      mb={0.5}
                      sx={{ fontSize: "12px" }}
                    >
                      {alert.flag_reason}
                    </MDTypography>
                    <MDTypography variant="caption" color="text" sx={{ fontSize: "11px" }}>
                      {formatDate(alert.created_at || alert.timestamp)}
                    </MDTypography>

                    {/* Acknowledge button for PENDING cards */}
                    {isPending && (
                      <MDBox mt={1.5}>
                        <MDButton
                          variant="gradient"
                          color="warning"
                          size="small"
                          fullWidth
                          onClick={() => handleAcknowledge(alert.id, alert.agent_id)}
                          sx={{ py: 0.5, fontSize: "11px" }}
                        >
                          ACKNOWLEDGE
                        </MDButton>
                      </MDBox>
                    )}
                  </MDBox>
                  {index < alerts.length - 1 && <Divider sx={{ my: 1.5 }} />}
                </MDBox>
              );
            })
          )}
        </MDBox>
      </MDBox>

      {/* Dynamic heartbeat styles for pulsating effect */}
      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.15); opacity: 0.7; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </Card>
  );
}

export default AlertPanel;
