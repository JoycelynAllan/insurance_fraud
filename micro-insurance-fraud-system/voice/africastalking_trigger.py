"""
Africa's Talking Voice & SMS Trigger Helper for MicroInsure Fraud System.
Provides localized automated payment reminders via Africa's Talking Voice and SMS API.
"""

import os
import logging
import africastalking

logger = logging.getLogger(__name__)

# Initialize Africa's Talking SDK
AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_API_KEY = os.getenv("AT_API_KEY", "")

africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms_client = africastalking.SMS
voice_client = africastalking.Voice

def trigger_voice_call(customer_phone: str, agent_id: str, amount: float, language: str = "twi"):
    """
    Triggers an outbound voice call or SMS reminder using Africa's Talking SDK.
    """
    logger.info(f"Triggering Africa's Talking voice/SMS reminder for {customer_phone} (Agent: {agent_id}, Amount: GHS {amount})")
    
    msg = f"MicroInsure Ghana: Your insurance premium of GHS {amount:.2f} is outstanding. Please contact agent {agent_id}."
    if language.lower() == "twi":
        msg = f"MicroInsure Ghana: Wo insurance premium a GHS {amount:.2f} nte ho. Fa sika no ko wo agent {agent_id} nkyen."
    elif language.lower() == "dagbani":
        msg = f"MicroInsure Ghana: A insurance puuni GHS {amount:.2f} bi ka. Sheri ni fo agent {agent_id} ka amoonin."

    try:
        response = sms_client.send(message=msg, recipients=[customer_phone])
        logger.info(f"Africa's Talking SMS response: {response}")
        return {"status": "success", "response": response}
    except Exception as e:
        logger.error(f"Africa's Talking trigger error: {str(e)}")
        return {"status": "error", "detail": str(e)}
