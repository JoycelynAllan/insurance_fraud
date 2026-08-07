import os
import random
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db import get_db
from backend.app.utils.auth_guard import get_current_user
from backend.app.models.user import User, OTPCode

logger = logging.getLogger(__name__)
router = APIRouter()

class OTPSendRequest(BaseModel):
    phone_number: str = Field(..., description="Destination phone number with country code, e.g. +233241234567")

class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(..., description="Destination phone number with country code")
    code: str = Field(..., description="6-digit verification OTP code")


def send_sms_via_africastalking(phone_number: str, message: str) -> dict:
    username = os.getenv("AT_USERNAME", "sandbox")
    api_key = os.getenv("AT_API_KEY")

    if not api_key or api_key.strip() in ["your_at_api_key_here", "your_africastalking_key", "<your_africastalking_key>", ""]:
        logger.info(f"[DEV SMS FALLBACK] AT_API_KEY missing or placeholder. Would send SMS to {phone_number}: {message}")
        return {"status": "dev_sandbox", "message": "Development fallback mode — SMS logged."}

    try:
        import africastalking
        africastalking.initialize(username, api_key.strip())
        sms = africastalking.SMS
        response = sms.send(message, [phone_number])
        logger.info(f"Africa's Talking SMS API Response for {phone_number}: {response}")
        
        # Log recipient status details
        if isinstance(response, dict):
            recipients = response.get("SMSMessageData", {}).get("Recipients", [])
            for r in recipients:
                logger.info(f"Recipient {r.get('number')}: status={r.get('status')}, cost={r.get('cost')}, msgId={r.get('messageId')}")

        return response
    except Exception as e:
        logger.error(f"Failed to send SMS via Africa's Talking for {phone_number}: {str(e)}")
        return {"status": "error", "detail": str(e)}


@router.get("/otp/status")
def get_otp_status(current_user: User = Depends(get_current_user)):
    return {
        "phone_number": current_user.phone_number,
        "phone_verified": current_user.phone_verified
    }


@router.post("/otp/send")
def send_otp(
    body: OTPSendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    phone = body.phone_number.strip()
    if not phone.startswith("+"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must include country code prefix, e.g. +233..."
        )

    # Generate 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Save to database
    otp_record = OTPCode(
        user_id=current_user.id,
        phone_number=phone,
        code=otp_code,
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    db.commit()

    # Dispatch SMS
    sms_message = f"Your MicroInsure Fraud Monitor verification code is: {otp_code}. Valid for 10 minutes."
    sms_result = send_sms_via_africastalking(phone, sms_message)

    return {
        "status": "success",
        "message": f"OTP verification code sent to {phone}",
        "dev_otp": otp_code if (os.getenv("AT_USERNAME", "sandbox") == "sandbox" or os.getenv("AT_API_KEY") in [None, "your_at_api_key_here"]) else None,
        "sms_result": sms_result
    }


@router.post("/otp/verify")
def verify_otp(
    body: OTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    phone = body.phone_number.strip()
    code = body.code.strip()

    # Find active unexpired OTP code
    otp_record = db.query(OTPCode).filter(
        OTPCode.user_id == current_user.id,
        OTPCode.phone_number == phone,
        OTPCode.code == code,
        OTPCode.is_used == False,
        OTPCode.expires_at >= datetime.utcnow()
    ).order_by(OTPCode.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP verification code."
        )

    # Mark OTP as used
    otp_record.is_used = True

    # Mark user phone as verified
    current_user.phone_number = phone
    current_user.phone_verified = True
    db.commit()

    return {
        "status": "success",
        "message": "Phone number verified successfully!",
        "phone_number": phone,
        "phone_verified": True
    }
