import FraudDashboard from "views/Dashboard/FraudDashboard";
import VoiceCampaigns from "views/Dashboard/VoiceCampaigns";
import AgentProfile from "views/AgentProfile";
import Login from "views/Auth/Login";
import Register from "views/Auth/Register";
import PrivateRoute from "utils/PrivateRoute";

// @mui icons
import Icon from "@mui/material/Icon";

const routes = [
  {
    type: "collapse",
    name: "Fraud Monitor",
    key: "fraud",
    icon: <Icon fontSize="small">warning</Icon>,
    route: "/fraud",
    component: (
      <PrivateRoute allowedRoles={["supervisor"]}>
        <FraudDashboard />
      </PrivateRoute>
    ),
  },
  {
    type: "collapse",
    name: "Voice Campaigns",
    key: "voice-campaigns",
    icon: <Icon fontSize="small">record_voice_over</Icon>,
    route: "/voice-campaigns",
    component: (
      <PrivateRoute allowedRoles={["supervisor"]}>
        <VoiceCampaigns />
      </PrivateRoute>
    ),
  },
  {
    type: "collapse",
    name: "My Profile",
    key: "agent-profile",
    icon: <Icon fontSize="small">person</Icon>,
    route: "/agent-profile",
    component: (
      <PrivateRoute>
        <AgentProfile />
      </PrivateRoute>
    ),
  },
  {
    type: "route",
    name: "Agent Detail Profile",
    key: "agent-profile-detail",
    route: "/agent-profile/:agentId",
    component: (
      <PrivateRoute>
        <AgentProfile />
      </PrivateRoute>
    ),
  },
  {
    type: "auth",
    name: "Login",
    key: "login",
    route: "/login",
    component: <Login />,
  },
  {
    type: "auth",
    name: "Register",
    key: "register",
    route: "/register",
    component: <Register />,
  },
];

export default routes;
