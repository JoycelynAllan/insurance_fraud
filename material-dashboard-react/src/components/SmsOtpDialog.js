import React, { useState, useEffect } from "react";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import CircularProgress from "@mui/material/CircularProgress";
import axios from "axios";

import MDBox from "components/MDBox";
import MDTypography from "components/MDTypography";
import MDInput from "components/MDInput";
import MDButton from "components/MDButton";
import MDBadge from "components/MDBadge";
import PropTypes from "prop-types";
import { getApiBase } from "utils/apiConfig";

function SmsOtpDialog({ open, onClose }) {
  const [step, setStep] = useState(1); // 1: Enter Phone, 2: Enter OTP
  const [phoneNumber, setPhoneNumber] = useState("+233");
  const [otpCode, setOtpCode] = useState("");
  const [statusInfo, setStatusInfo] = useState({ phone_number: null, phone_verified: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [devOtpHint, setDevOtpHint] = useState(null);

  const fetchStatus = async () => {
    try {
      const apiBase = getApiBase();
      const res = await axios.get(`${apiBase}/api/otp/status`);
      setStatusInfo(res.data);
      if (res.data.phone_number) {
        setPhoneNumber(res.data.phone_number);
      }
    } catch (e) {
      console.error("Failed to fetch OTP status:", e);
    }
  };

  useEffect(() => {
    if (open) {
      fetchStatus();
      setError("");
      setMessage("");
      setDevOtpHint(null);
      setStep(1);
    }
  }, [open]);

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setDevOtpHint(null);
    setLoading(true);

    try {
      const apiBase = getApiBase();
      const res = await axios.post(`${apiBase}/api/otp/send`, {
        phone_number: phoneNumber,
      });

      setMessage(res.data.message || "OTP code sent via SMS!");
      if (res.data.dev_otp) {
        setDevOtpHint(res.data.dev_otp);
      }
      setStep(2);
    } catch (err) {
      console.error("[OTP Send Error]", err);
      const detail =
        err.response?.data?.detail || "Failed to send OTP. Ensure phone includes +233 prefix.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      const apiBase = getApiBase();
      const res = await axios.post(`${apiBase}/api/otp/verify`, {
        phone_number: phoneNumber,
        code: otpCode,
      });

      setMessage(res.data.message || "Phone number verified successfully!");
      setStatusInfo({ phone_number: phoneNumber, phone_verified: true });
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      console.error("[OTP Verify Error]", err);
      const detail =
        err.response?.data?.detail || "Invalid verification code. Please check and try again.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <MDTypography variant="h6" fontWeight="bold">
          SMS OTP Verification
        </MDTypography>
        {statusInfo.phone_verified ? (
          <MDBadge badgeContent="VERIFIED" color="success" variant="gradient" size="xs" />
        ) : (
          <MDBadge badgeContent="UNVERIFIED" color="warning" variant="gradient" size="xs" />
        )}
      </DialogTitle>
      <DialogContent dividers>
        {error && (
          <MDBox mb={2} p={1} borderRadius="md" bgColor="error" color="white">
            <MDTypography variant="caption" color="white" fontWeight="medium">
              {error}
            </MDTypography>
          </MDBox>
        )}
        {message && (
          <MDBox mb={2} p={1} borderRadius="md" bgColor="success" color="white">
            <MDTypography variant="caption" color="white" fontWeight="medium">
              {message}
            </MDTypography>
          </MDBox>
        )}

        {devOtpHint && (
          <MDBox mb={2} p={1} borderRadius="md" bgColor="info" color="white" textAlign="center">
            <MDTypography variant="caption" color="white" fontWeight="bold">
              [DEV MODE] Generated OTP: {devOtpHint}
            </MDTypography>
          </MDBox>
        )}

        {step === 1 ? (
          <MDBox component="form" onSubmit={handleSendOtp} pt={1}>
            <MDTypography variant="caption" color="text" display="block" mb={2}>
              Enter your mobile phone number with country code (e.g. +233 for Ghana) to receive SMS
              alert notifications.
            </MDTypography>
            <MDInput
              type="text"
              label="Phone Number (E.164 format)"
              fullWidth
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+233241234567"
              required
            />
            <MDBox mt={3}>
              <MDButton variant="gradient" color="info" fullWidth type="submit" disabled={loading}>
                {loading ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  "Send SMS Verification Code"
                )}
              </MDButton>
            </MDBox>
          </MDBox>
        ) : (
          <MDBox component="form" onSubmit={handleVerifyOtp} pt={1}>
            <MDTypography variant="caption" color="text" display="block" mb={2}>
              A 6-digit OTP verification code was sent to <strong>{phoneNumber}</strong>.
            </MDTypography>
            <MDInput
              type="text"
              label="6-Digit OTP Code"
              fullWidth
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
              placeholder="123456"
              required
            />
            <MDBox mt={3} display="flex" justifyContent="space-between">
              <MDButton
                variant="outlined"
                color="secondary"
                size="small"
                onClick={() => setStep(1)}
              >
                Change Phone
              </MDButton>
              <MDButton variant="gradient" color="success" type="submit" disabled={loading}>
                {loading ? <CircularProgress size={16} color="inherit" /> : "Verify Code"}
              </MDButton>
            </MDBox>
          </MDBox>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 1.5 }}>
        <MDButton variant="text" color="secondary" onClick={onClose}>
          Close
        </MDButton>
      </DialogActions>
    </Dialog>
  );
}

SmsOtpDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default SmsOtpDialog;
