"""PayPal Sandbox REST API Client with Server-Side Verification and Idempotency."""
import uuid
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings


class PayPalConfigurationError(Exception):
    """Raised when PayPal credentials are not configured or are invalid."""
    pass


class PayPalApiError(Exception):
    """Raised when PayPal returns an error response."""
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class PayPalTimeoutError(Exception):
    """Raised when connection to PayPal times out."""
    pass


class PayPalService:
    """Client for interacting with the PayPal Sandbox REST API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        currency: Optional[str] = None,
        timeout_seconds: float = 10.0
    ):
        self.client_id = client_id or settings.PAYPAL_CLIENT_ID
        self.client_secret = client_secret or settings.PAYPAL_CLIENT_SECRET
        self.base_url = (base_url or settings.PAYPAL_BASE_URL).rstrip("/")
        self.currency = currency or settings.PAYPAL_CURRENCY
        self.timeout_seconds = timeout_seconds

    def is_configured(self) -> bool:
        """Check if non-placeholder PayPal credentials are configured."""
        if not self.client_id or not self.client_secret:
            return False
        if "placeholder" in self.client_id.lower() or "placeholder" in self.client_secret.lower():
            return False
        return True

    def get_access_token(self) -> str:
        """Obtain an OAuth2 access token using HTTP Basic authentication.

        Never logs client secrets.
        """
        if not self.is_configured():
            raise PayPalConfigurationError("PayPal Sandbox credentials are not configured on the server.")

        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    url,
                    headers=headers,
                    data=data,
                    auth=(self.client_id, self.client_secret)
                )

            if response.status_code != 200:
                raise PayPalApiError(
                    f"PayPal authentication failed with status {response.status_code}",
                    status_code=response.status_code,
                    details=response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                )

            token_data = response.json()
            return token_data["access_token"]
        except httpx.TimeoutException as e:
            raise PayPalTimeoutError(f"Connection to PayPal timed out during authentication: {e}")
        except httpx.RequestError as e:
            raise PayPalApiError(f"Network error communicating with PayPal: {e}")

    def create_paypal_order(
        self,
        amount_str: str,
        currency: str,
        reference_id: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a PayPal order for capture intent.

        Uses PayPal-Request-Id for idempotency.
        """
        token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders"
        request_id = idempotency_key or str(uuid.uuid4())

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": request_id,
        }

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": reference_id,
                    "amount": {
                        "currency_code": currency,
                        "value": amount_str
                    }
                }
            ]
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)

            if response.status_code not in (200, 201):
                err_body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_body.get("message") or f"PayPal order creation failed with status {response.status_code}"
                raise PayPalApiError(err_msg, status_code=response.status_code, details=err_body)

            return response.json()
        except httpx.TimeoutException as e:
            raise PayPalTimeoutError(f"PayPal order creation timed out: {e}")
        except httpx.RequestError as e:
            raise PayPalApiError(f"Network error communicating with PayPal: {e}")

    def capture_paypal_order(
        self,
        paypal_order_id: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Capture funds for an approved PayPal order.

        Uses PayPal-Request-Id for idempotency.
        """
        token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders/{paypal_order_id}/capture"
        request_id = idempotency_key or str(uuid.uuid4())

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": request_id,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=headers, json={})

            if response.status_code not in (200, 201):
                err_body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_body.get("message") or f"PayPal capture failed with status {response.status_code}"
                raise PayPalApiError(err_msg, status_code=response.status_code, details=err_body)

            return response.json()
        except httpx.TimeoutException as e:
            raise PayPalTimeoutError(f"PayPal capture timed out: {e}")
        except httpx.RequestError as e:
            raise PayPalApiError(f"Network error communicating with PayPal: {e}")


# Default global instance
paypal_service = PayPalService()
