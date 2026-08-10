import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

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

          // Update alerts list deduplicated by agent_id and sorted by risk_score desc
          setAlerts((prevAlerts) => {
            const filtered = prevAlerts.filter((a) => a.agent_id !== data.agent_id);
            const updated = [data, ...filtered];
            updated.sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));
            return updated;
          });
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
        prev.map((a) => (a.agent_id === agentId ? { ...a, status: "INVESTIGATING" } : a))
      );
    } catch (err) {
      console.error("Error acknowledging alert:", err);
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
          {alerts.length === 0 ? (
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
              const numericScore = typeof alert.risk_score === "number" ? alert.risk_score : parseFloat(alert.risk_score) || 0;
              const scorePct = numericScore <= 1.0 ? numericScore * 100 : numericScore;
              const isHighRisk = scorePct >= 70.0;
              const isPending = (alert.status || "PENDING").toUpperCase() === "PENDING";

              return (
                <MDBox key={alert.agent_id || index} mb={2}>
                  <MDBox
                    p={2}
                    borderRadius="lg"
                    sx={{
                      border: "1px solid",
                      borderColor: isHighRisk ? "error.main" : "warning.main",
                      backgroundColor: isHighRisk ? "rgba(244, 67, 54, 0.04)" : "rgba(255, 152, 0, 0.04)",
                    }}
                  >
                    <MDBox display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <MDBox display="flex" alignItems="center">
                        <MDTypography variant="button" fontWeight="bold" color="dark" sx={{ mr: 1 }}>
                          {alert.agent_id}
                        </MDTypography>
                        <MDBadge
                          badgeContent={alert.status || "PENDING"}
                          color={getBadgeColor(alert.status)}
                          variant="gradient"
                          size="xs"
                        />
                      </MDBox>
                      <MDTypography variant="caption" color="text" fontWeight="medium">
                        {formatDate(alert.created_at || alert.timestamp)}
                      </MDTypography>
                    </MDBox>
                    <MDTypography
                      variant="caption"
                      color="dark"
                      fontWeight="medium"
                      display="block"
                      mb={0.5}
                    >
                      {alert.flag_reason}
                    </MDTypography>
                    <MDBox display="flex" justifyContent="space-between" alignItems="center" mt={1}>
                      <MDTypography variant="caption" color="text">
                        Risk Score:
                      </MDTypography>
                      <MDTypography
                        variant="caption"
                        color={isHighRisk ? "error" : "warning"}
                        fontWeight="bold"
                        sx={{ fontSize: "0.95rem" }}
                      >
                        {scorePct.toFixed(1)}%
                      </MDTypography>
                    </MDBox>

                    {/* Acknowledge button for PENDING cards */}
                    {isPending && (
                      <MDBox mt={1.5} display="flex" justifyContent="flex-end">
                        <MDButton
                          variant="gradient"
                          color="warning"
                          size="small"
                          onClick={() => handleAcknowledge(alert.id, alert.agent_id)}
                          sx={{ py: 0.3, px: 1.5, fontSize: "0.65rem" }}
                        >
                          Acknowledge
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
