import os
from app.core.config import settings

class PowerBIService:
    def __init__(self):
        if settings.POWERBI_MOCK_MODE:
            print("⚠️ MOCK MODE: PowerBIService uses mock token.")
            self.token = "mock-token"
            return  # ⛔ MSAL çağrıları yapılmaz

        import msal
        self.app = msal.ConfidentialClientApplication(
            client_id=settings.POWERBI_CLIENT_ID,
            client_credential=settings.POWERBI_CLIENT_SECRET,
            authority=settings.POWERBI_AUTHORITY
        )
        self.token = self._acquire_token()

    def _acquire_token(self):
        result = self.app.acquire_token_for_client(scopes=[settings.POWERBI_SCOPE])
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception("Unable to acquire Power BI token")

powerbi_service = PowerBIService()