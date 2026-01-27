"""Client for interacting with pets-backend GraphQL API."""

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.exceptions import PetsBackendError

_logger = logging.getLogger(__name__)


class PetsBackendClient:
    """Client for pets-backend GraphQL API."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
    ):
        """Initialize pets-backend client.

        Args:
            base_url: Base URL of pets-backend GraphQL server
            timeout: Request timeout in seconds
        """
        self._base_url = base_url.rstrip("/")
        self._graphql_url = f"{self._base_url}/graphql"
        self._timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with pets-backend using Firebase Admin.

        Note: pets-backend uses Firebase Admin for token verification.
        This method attempts to verify via GraphQL, but if that's not available,
        you may need to verify the token directly using Firebase Admin SDK.

        Args:
            token: JWT token to verify

        Returns:
            User information if token is valid

        Raises:
            PetsBackendError: If verification fails
        """
        # Since pets-backend uses Firebase Admin, we can verify tokens
        # by checking with the backend's auth context
        # For now, we'll use a simple GraphQL query to get user info
        query = """
        query GetUser {
            me {
                id
                email
            }
        }
        """
        
        try:
            if not self._http_client:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        self._graphql_url,
                        json={"query": query},
                        headers=self._headers(token=token),
                    )
            else:
                response = await self._http_client.post(
                    self._graphql_url,
                    json={"query": query},
                    headers=self._headers(token=token),
                )
            
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                raise PetsBackendError(f"GraphQL errors: {data['errors']}")
            
            user_data = data.get("data", {}).get("me", {})
            if not user_data:
                raise PetsBackendError("Token verification failed: No user data")
            
            return user_data
            
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise PetsBackendError("Token verification failed: Unauthorized")
            raise PetsBackendError(
                f"pets-backend verification failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise PetsBackendError(f"pets-backend connection error: {exc}") from exc

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Get user information from pets-backend.

        Args:
            token: JWT token

        Returns:
            User information
        """
        query = """
        query GetUser {
            me {
                id
                email
                name
            }
        }
        """
        
        try:
            if not self._http_client:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        self._graphql_url,
                        json={"query": query},
                        headers=self._headers(token=token),
                    )
            else:
                response = await self._http_client.post(
                    self._graphql_url,
                    json={"query": query},
                    headers=self._headers(token=token),
                )
            
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                raise PetsBackendError(f"GraphQL errors: {data['errors']}")
            
            return data.get("data", {}).get("me", {})
            
        except httpx.HTTPStatusError as exc:
            raise PetsBackendError(
                f"pets-backend request failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise PetsBackendError(f"pets-backend connection error: {exc}") from exc
