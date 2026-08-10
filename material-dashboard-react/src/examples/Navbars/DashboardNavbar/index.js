/**
=========================================================
* Material Dashboard 2 React - v2.2.0
=========================================================

* Product Page: https://www.creative-tim.com/product/material-dashboard-react
* Copyright 2023 Creative Tim (https://www.creative-tim.com)

Coded by www.creative-tim.com

 =========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
*/

import { useState, useEffect } from "react";

// react-router components
import { useLocation, Link, useNavigate } from "react-router-dom";
import axios from "axios";

// prop-types is a library for typechecking of props.
import PropTypes from "prop-types";

// @material-ui core components
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import Icon from "@mui/material/Icon";

// Material Dashboard 2 React components
import MDBox from "components/MDBox";
import MDInput from "components/MDInput";
import MDTypography from "components/MDTypography";

// Material Dashboard 2 React example components
import Breadcrumbs from "examples/Breadcrumbs";
import NotificationItem from "examples/Items/NotificationItem";

// Custom styles for DashboardNavbar
import {
  navbar,
  navbarContainer,
  navbarRow,
  navbarIconButton,
  navbarMobileMenu,
} from "examples/Navbars/DashboardNavbar/styles";

// Material Dashboard 2 React context
import {
  useMaterialUIController,
  setTransparentNavbar,
  setMiniSidenav,
  setOpenConfigurator,
} from "context";

import SmsOtpDialog from "components/SmsOtpDialog";

import { getApiBase } from "utils/apiConfig";

function DashboardNavbar({ absolute, light, isMini, title, showGhanaTime }) {
  const [navbarType, setNavbarType] = useState();
  const [controller, dispatch] = useMaterialUIController();
  const { miniSidenav, transparentNavbar, fixedNavbar, openConfigurator, darkMode } = controller;
  const [openMenu, setOpenMenu] = useState(false);
  const [otpOpen, setOtpOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const navigate = useNavigate();
  const token = localStorage.getItem("mifds_token");
  const userName = localStorage.getItem("mifds_user_name") || "User";

  // Fetch real notifications (Fraud Alerts & Voice IVR Confirmations)
  useEffect(() => {
    let isMounted = true;
    const fetchNotifications = async () => {
      if (!token) return;
      try {
        const apiBase = getApiBase();
        const authHeaders = { headers: { Authorization: `Bearer ${token}` } };

        const [alertsRes, voiceRes] = await Promise.allSettled([
          axios.get(`${apiBase}/api/alerts?limit=3`, authHeaders),
          axios.get(`${apiBase}/api/voice/logs?limit=3`, authHeaders),
        ]);

        const items = [];
        if (alertsRes.status === "fulfilled" && alertsRes.value.data?.alerts) {
          alertsRes.value.data.alerts.forEach((alert) => {
            items.push({
              id: `alert-${alert.id}`,
              type: "alert",
              title: `Fraud Alert: ${alert.agent_id}`,
              subtitle: `${alert.flag_reason} (Risk: ${alert.risk_score}%)`,
              icon: "warning",
              route: "/fraud",
            });
          });
        }

        if (voiceRes.status === "fulfilled" && voiceRes.value.data?.logs) {
          voiceRes.value.data.logs.forEach((log) => {
            if (log.outcome === "payment_confirmed_by_customer") {
              items.push({
                id: `voice-${log.id}`,
                type: "voice",
                title: `Payment Confirmed: ${log.customer_phone}`,
                subtitle: `GHS ${log.amount} confirmed via Voice IVR`,
                icon: "check_circle",
                route: "/voice-campaigns",
              });
            }
          });
        }

        if (isMounted && items.length > 0) {
          setNotifications(items.slice(0, 5));
        }
      } catch (err) {
        console.error("Failed to fetch notification items:", err);
      }
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [token]);

  const handleLogout = async () => {
    try {
      const apiBase = getApiBase();
      await axios.post(`${apiBase}/api/auth/logout`);
    } catch (err) {
      console.error("Logout API call failed:", err);
    } finally {
      localStorage.removeItem("mifds_token");
      localStorage.removeItem("mifds_user_name");
      localStorage.removeItem("mifds_user_role");
      navigate("/login");
    }
  };
  const route = useLocation().pathname.split("/").slice(1);
  const [ghanaTime, setGhanaTime] = useState("");

  useEffect(() => {
    if (showGhanaTime) {
      const updateTime = () => {
        const now = new Date();
        const options = {
          timeZone: "UTC",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        };
        const timeString = now.toLocaleTimeString("en-GB", options);
        setGhanaTime(`${timeString} (GMT+0)`);
      };
      updateTime();
      const interval = setInterval(updateTime, 1000);
      return () => clearInterval(interval);
    }
  }, [showGhanaTime]);

  useEffect(() => {
    if (fixedNavbar) {
      setNavbarType("sticky");
    } else {
      setNavbarType("static");
    }

    function handleTransparentNavbar() {
      setTransparentNavbar(dispatch, (fixedNavbar && window.scrollY === 0) || !fixedNavbar);
    }

    window.addEventListener("scroll", handleTransparentNavbar);
    handleTransparentNavbar();
    return () => window.removeEventListener("scroll", handleTransparentNavbar);
  }, [dispatch, fixedNavbar]);

  const handleMiniSidenav = () => setMiniSidenav(dispatch, !miniSidenav);
  const handleConfiguratorOpen = () => setOpenConfigurator(dispatch, !openConfigurator);
  const handleOpenMenu = (event) => setOpenMenu(event.currentTarget);
  const handleCloseMenu = () => setOpenMenu(false);

  const handleNotificationClick = (targetRoute) => {
    handleCloseMenu();
    if (targetRoute) {
      navigate(targetRoute);
    }
  };

  // Render the notifications menu with real data
  const renderMenu = () => (
    <Menu
      anchorEl={openMenu}
      anchorReference={null}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "left",
      }}
      open={Boolean(openMenu)}
      onClose={handleCloseMenu}
      sx={{ mt: 2 }}
    >
      {notifications.length === 0 ? (
        <NotificationItem
          icon={<Icon>notifications_none</Icon>}
          title="No active fraud notifications"
        />
      ) : (
        notifications.map((item) => (
          <NotificationItem
            key={item.id}
            icon={<Icon>{item.icon}</Icon>}
            title={`${item.title} - ${item.subtitle}`}
            onClick={() => handleNotificationClick(item.route)}
          />
        ))
      )}
    </Menu>
  );

  // Styles for the navbar icons
  const iconsStyle = ({ palette: { dark, white, text }, functions: { rgba } }) => ({
    color: () => {
      let colorValue = light || darkMode ? white.main : dark.main;

      if (transparentNavbar && !light) {
        colorValue = darkMode ? rgba(text.main, 0.6) : text.main;
      }

      return colorValue;
    },
  });

  const userRole = localStorage.getItem("mifds_user_role") || "supervisor";
  const formattedRoleName = userRole === "agent" ? "Agent" : "Supervisor";

  return (
    <AppBar
      position={absolute ? "absolute" : navbarType}
      color="inherit"
      sx={(theme) => navbar(theme, { transparentNavbar, absolute, light, darkMode })}
    >
      <Toolbar sx={(theme) => navbarContainer(theme)}>
        <MDBox color="inherit" mb={{ xs: 1, md: 0 }} sx={(theme) => navbarRow(theme, { isMini })}>
          <Breadcrumbs
            icon="home"
            title={title || route[route.length - 1]}
            route={route}
            light={light}
          />
        </MDBox>
        {isMini ? null : (
          <MDBox sx={(theme) => navbarRow(theme, { isMini })}>
            <MDBox pr={1}>
              <MDInput label="Search here" />
            </MDBox>
            <MDBox color={light ? "white" : "inherit"} display="flex" alignItems="center">
              {showGhanaTime && ghanaTime && (
                <MDBox mr={2}>
                  <MDTypography
                    variant="button"
                    color={light ? "white" : "text"}
                    fontWeight="medium"
                  >
                    🇬🇭 {ghanaTime}
                  </MDTypography>
                </MDBox>
              )}
              {token ? (
                <MDBox display="flex" alignItems="center" mr={2}>
                  <MDTypography
                    variant="button"
                    color={light ? "white" : "text"}
                    fontWeight="medium"
                    sx={{ mr: 1, display: "flex", alignItems: "center" }}
                  >
                    <Icon sx={{ mr: 0.5 }}>account_circle</Icon>
                    {userName} — Supervisor
                  </MDTypography>
                  <IconButton
                    sx={navbarIconButton}
                    size="small"
                    onClick={() => setOtpOpen(true)}
                    title="SMS OTP Phone Verification"
                  >
                    <Icon sx={{ color: "info.main", mr: 0.5 }}>sms</Icon>
                  </IconButton>
                  <IconButton
                    sx={navbarIconButton}
                    size="small"
                    onClick={handleLogout}
                    title="Logout"
                  >
                    <Icon sx={{ color: "error.main" }}>logout</Icon>
                  </IconButton>
                </MDBox>
              ) : (
                <Link to="/login">
                  <IconButton sx={navbarIconButton} size="small" disableRipple>
                    <Icon sx={iconsStyle}>account_circle</Icon>
                  </IconButton>
                </Link>
              )}
              <IconButton
                size="small"
                disableRipple
                color="inherit"
                sx={navbarMobileMenu}
                onClick={handleMiniSidenav}
              >
                <Icon sx={iconsStyle} fontSize="medium">
                  {miniSidenav ? "menu_open" : "menu"}
                </Icon>
              </IconButton>
              <IconButton
                size="small"
                disableRipple
                color="inherit"
                sx={navbarIconButton}
                onClick={handleConfiguratorOpen}
              >
                <Icon sx={iconsStyle}>settings</Icon>
              </IconButton>
              <IconButton
                size="small"
                disableRipple
                color="inherit"
                sx={navbarIconButton}
                aria-controls="notification-menu"
                aria-haspopup="true"
                variant="contained"
                onClick={handleOpenMenu}
              >
                <Icon sx={iconsStyle}>notifications</Icon>
              </IconButton>
              {renderMenu()}
            </MDBox>
          </MDBox>
        )}
      </Toolbar>
      <SmsOtpDialog open={otpOpen} onClose={() => setOtpOpen(false)} />
    </AppBar>
  );
}

// Setting default values for the props of DashboardNavbar
DashboardNavbar.defaultProps = {
  absolute: false,
  light: false,
  isMini: false,
  title: "",
  showGhanaTime: false,
};

// Typechecking props for the DashboardNavbar
DashboardNavbar.propTypes = {
  absolute: PropTypes.bool,
  light: PropTypes.bool,
  isMini: PropTypes.bool,
  title: PropTypes.string,
  showGhanaTime: PropTypes.bool,
};

export default DashboardNavbar;
