import os
from unittest.mock import patch
from fastapi.testclient import TestClient
import africastalking

from backend.app.main import app
from backend.app.services.voice_service import schedule_retry, AUDIO_URLS

client = TestClient(app)

def run_sms_test():
    """
    Standalone function to test SMS sending via Africa's Talking.
    """
    at_username = os.environ.get("AT_USERNAME", "sandbox")
    at_api_key = os.environ.get("AT_API_KEY", "")
    
    africastalking.initialize(at_username, at_api_key)
    sms = africastalking.SMS
    
    try:
        response = sms.send(
            message="MicroInsure Ghana TEST: This is a test reminder. Your premium payment is outstanding.",
            recipients=["+254711XXXYYY"]
        )
        print("AT SMS Response:", response)
        if isinstance(response, dict) and "SMSMessageData" in response:
            print("SMS TEST PASSED")
        else:
            print(f"SMS TEST FAILED: {response}")
    except Exception as e:
        print(f"SMS TEST FAILED: {str(e)}")

def test_voice_retry_stops_at_3():
    with patch("backend.app.services.voice_service.send_payment_reminder") as mock_send:
        schedule_retry("+233200000000", "AGT001", 50.0, "twi", attempt=4)
        mock_send.assert_not_called()
        print("RETRY LIMIT TEST PASSED")

def test_voice_callback_dtmf_1():
    response = client.post(
        "/api/voice/callback",
        data={
            "dtmfDigits": "1",
            "callerNumber": "+233200000000",
            "sessionId": "test123",
            "language": "twi"
        }
    )
    assert response.status_code == 200
    assert "Thank you for confirming" in response.text
    assert "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/twi_confirm.mp3" in response.text
    print("DTMF 1 TEST PASSED")

def test_voice_callback_dtmf_2():
    response = client.post(
        "/api/voice/callback",
        data={
            "dtmfDigits": "2",
            "callerNumber": "+233200000000",
            "sessionId": "test124",
            "language": "twi"
        }
    )
    assert response.status_code == 200
    assert "support agent" in response.text
    print("DTMF 2 TEST PASSED")

def test_voice_callback_no_dtmf():
    response = client.post(
        "/api/voice/callback",
        data={
            "dtmfDigits": "",
            "callerNumber": "+233200000000",
            "sessionId": "test125",
            "language": "twi"
        }
    )
    assert response.status_code == 200
    assert "Play" in response.text
    assert "GetDigits" in response.text
    assert "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/twi_reminder.mp3" in response.text
    print("NO DTMF TEST PASSED")

def test_dagbani_audio_urls():
    assert AUDIO_URLS["dagbani"]["reminder"] == "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/dagbani_reminder.mp3"
    assert AUDIO_URLS["dagbani"]["confirm"] == "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/dagbani_confirm.mp3"
    assert AUDIO_URLS["twi"]["reminder"] == "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/twi_reminder.mp3"
    assert AUDIO_URLS["twi"]["confirm"] == "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/twi_confirm.mp3"
    print("AUDIO URL TEST PASSED")
