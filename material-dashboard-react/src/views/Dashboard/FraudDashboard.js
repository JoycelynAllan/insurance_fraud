import React, { useState } from "react";

// @mui material components
import Grid from "@mui/material/Grid";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";

// Material Dashboard 2 React example components
import DashboardLayout from "examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "examples/Navbars/DashboardNavbar";
import Footer from "examples/Footer";

// Custom Fraud monitoring components
import AgentRiskTable from "components/AgentRiskTable";
import AlertPanel from "components/AlertPanel";
import BranchHeatmap from "components/BranchHeatmap";
import PaymentTrendChart from "components/PaymentTrendChart";

function FraudDashboard() {
  const [selectedAgentId, setSelectedAgentId] = useState("AGT001");

  return (
    <DashboardLayout>
      <DashboardNavbar title="MicroInsure Fraud Monitor" showGhanaTime />
      <MDBox py={3}>
        {/* Top Row: Agent Risk Table & Real-Time Alerts */}
        <MDBox mb={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} lg={8}>
              <AgentRiskTable
                selectedAgentId={selectedAgentId}
                onSelectAgent={setSelectedAgentId}
              />
            </Grid>
            <Grid item xs={12} lg={4}>
              <AlertPanel />
            </Grid>
          </Grid>
        </MDBox>

        {/* Bottom Row: Branch Heatmap & Payment Trend Chart */}
        <MDBox>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6} lg={6}>
              <BranchHeatmap />
            </Grid>
            <Grid item xs={12} md={6} lg={6}>
              <PaymentTrendChart agentId={selectedAgentId} />
            </Grid>
          </Grid>
        </MDBox>
      </MDBox>
      <Footer />
    </DashboardLayout>
  );
}

export default FraudDashboard;
