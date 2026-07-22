import FraudDashboard from "views/Dashboard/FraudDashboard";
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
      <PrivateRoute>
        <FraudDashboard />
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
