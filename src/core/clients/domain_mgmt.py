import logging
import warnings
from typing import Any, Dict, List, Optional

import httpx
from urllib3.exceptions import InsecureRequestWarning

log = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=InsecureRequestWarning)  # annoying


class DomainMgmtApiClient:
    """Client for interacting with the Onboarding API (but UI on Domain Management).

    Handles authentication, token management, and standard HTTP request execution. Provides methods for sending requests with JSON bodies, file uploads, and optional authentication headers.

    Attributes:
        base_url (str): Base URL for the onboarding API.
        email (str): Admin user's email.
        password (str): Admin user's password.
        session (httpx.Client): HTTP client used to perform requests.
        _auth_token (Optional[str]): Token for partner-level API access.
        _customer_auth_token (Optional[str]): Token for customer-level API access.
    """

    def __init__(self, base_url: str, email: str, password: str):
        """Initializes the DomainMgmt API client.

        Sets up the HTTP session and stores credentials for future requests.

        Args:
            base_url (str): Base URL for the onboarding API.
            email (str): Admin user's email.
            password (str): Admin user's password.
        """
        self.base_url = base_url
        self.email = email
        self.password = password
        self.session = httpx.Client(verify=False)
        self._auth_token: Optional[str] = None
        self._customer_auth_token: Optional[str] = None
        log.debug(f"Onboarding API client initialized for URL: {self.base_url}")

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        expected_key: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
    ) -> Any:
        """Internal helper to make HTTP requests.

        Supports JSON requests, file uploads (with additional metadata), query parameters, and token-authenticated requests.

        Args:
            method (str): HTTP method (e.g., 'get', 'post', etc.).
            path (str): Endpoint path, appended to the base URL.
            token (Optional[str]): JWT for Authorization header.
            params (Optional[Dict[str, Any]]): Query string parameters.
            json_data (Optional[Dict[str, Any]]): JSON body payload.
            expected_key (Optional[str]): If provided, return response_json[expected_key].
            timeout (Optional[httpx.Timeout]): Timeout override for the request.

        Returns:
            Any: Full JSON response, or a nested key if `expected_key` is provided.
        """
        url = f"{self.base_url}{path}"
        headers: Dict[str, str] = {}

        if json_data is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Token {token}"
        log.debug(f"Request headers: {headers}")
        log.debug(f"{method.upper()} {url}")

        timeout = timeout or httpx.Timeout(30.0)
        resp = self.session.request(
            method,
            url,
            params=params,
            headers=headers,
            json=json_data,
            timeout=timeout,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            log.error(f"HTTP {resp.status_code} on {url}: {resp.text}")
            raise

        # Safely handle no-content / empty-body responses
        if resp.status_code == 204 or not resp.text.strip():
            # For DELETE (or any no-content), return None or empty dict
            return {} if expected_key else None

        # Otherwise, attempt JSON decode but catch failures
        try:
            data = resp.json()
        except ValueError:
            # Body wasn’t valid JSON; swallow and return None/{}
            return {} if expected_key else None

        # If caller asked for a sub-key, pull it out (default to {})
        if expected_key:
            return data.get(expected_key, {})

        return data

    # ==== Authentication ==============================================================

    def authenticate(self) -> str:
        """Authenticates with the onboarding API and caches the JWT access token.

        Returns:
            str: The JSON Web Token (JWT).
        """
        payload = {"email": self.email, "password": self.password}
        data = self._request("post", "/api/user/signin", json_data=payload)
        token = data.get("token")
        if not token:
            raise RuntimeError("Authentication succeeded but no token in response")
        self._auth_token = token
        log.info("Authentication successful. Token cached.")
        log.debug(f"Authenticated token: {token}")

    def generate_customer_token(self, customer_email: str) -> str:
        """Generates a session token for a specific customer."""
        data = self._request(
            "post",
            "/api/onboarding/partner/generate-client-token",
            token=self._auth_token,
            json_data={"email": customer_email},
        )
        token = data.get("token")
        if not token:
            raise RuntimeError("No customer token found in response")
        log.debug(f"Customer token generated: {token}")
        self._customer_auth_token = token

    # === Industry Details =============================================================

    def list_industries(self) -> List[Dict[str, Any]]:
        """Retrieves all available industries (model templates)."""
        return self._request(
            "get",
            "/api/industry",
            token=self._auth_token,
            expected_key="data",
        )

    def list_industry_categories(self) -> List[Dict[str, Any]]:
        """Retrieves all available industry categories (model templates)."""
        return self._request(
            "get",
            "/api/industry/category",
            token=self._auth_token,
            expected_key="data",
        )

    def get_industry_details(self, industry_id: int) -> Dict[str, Any]:
        """Retrieves detailed configuration for a specific industry/model."""
        return self._request(
            "get",
            f"/api/industry/{industry_id}",
            token=self._auth_token,
            expected_key="data",
        )

    # === Model Validation =============================================================

    def list_kpis(self, industry_id: int) -> List[Dict[str, Any]]:
        """Lists all KPIs available for the customer."""
        return self._request(
            "get",
            f"/api/industry-all-kpi/{industry_id}",
            token=self._auth_token,
            params={"type": 1},
        )

    def list_functions(self) -> List[Dict[str, Any]]:
        """Lists all functions."""
        return self._request(
            "get", "/api/function", token=self._auth_token, expected_key="data"
        )

    def list_contexts(self) -> List[Dict[str, Any]]:
        """Lists all context types available for the customer."""
        return self._request(
            "get", "/api/contextTypes", token=self._auth_token, expected_key="data"
        )

    def industry_metric_functions(self, industry_id: int) -> List[Dict[str, Any]]:
        """Lists all context types available for the customer."""
        return self._request(
            "get",
            f"/api/industry-metric/function/{industry_id}",
            token=self._auth_token,
            expected_key="data",
        )

    def get_dictionary_list(self, function_code: str) -> List[Dict[str, Any]]:
        """Gets the list of dictionaries for a given function code."""
        return self._request(
            "get",
            f"/api/domains/dictionaryList/{function_code}",
            token=self._auth_token,
            expected_key="data",
        )

    def get_dictionary(
        self,
        function_code: str,
    ) -> List[Dict[str, Any]]:
        """Gets the list of dictionaries for a given function code."""
        return self._request(
            "post",
            "/api/domains/getDictionary",
            token=self._auth_token,
            json_data={"functionCode": function_code},
        )
