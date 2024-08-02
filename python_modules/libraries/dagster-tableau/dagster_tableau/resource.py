from typing import Any, Dict, Tuple

import requests
from dagster import ConfigurableResource
from dagster._core.execution.context.init import InitResourceContext
from pydantic import PrivateAttr

BASE_API_URL = "https://{pod}.online.tableau.com/api/3.4"


class TableauSite(ConfigurableResource):
    """A resource used to interact with the Tableau API."""

    tableau_pod: str
    personal_access_token_name: str
    personal_access_token_secret: str
    site_content_url: str
    _api_token: str = PrivateAttr()
    _site_id: str = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._api_token, self._site_id = self._fetch_api_token_and_site_id()

    def fetch_json(self, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        """Fetch JSON data from the Tableau API. Raises an exception if the request fails.

        Args:
            endpoint (str): The API endpoint to fetch data from.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tableau-Auth": f"{self._api_token}",
        }
        response = requests.request(
            url=f"{BASE_API_URL.format(pod=self.tableau_pod)}/sites/{self._site_id}/{endpoint}",
            headers=headers,
            method=method,
        )
        response.raise_for_status()
        return response.json()

    def _fetch_api_token_and_site_id(self) -> Tuple[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = requests.post(
            url=f"{BASE_API_URL.format(pod=self.tableau_pod)}/auth/signin",
            headers=headers,
            json={
                "credentials": {
                    "personalAccessTokenName": self.personal_access_token_name,
                    "personalAccessTokenSecret": self.personal_access_token_secret,
                    "site": {"contentUrl": self.site_content_url},
                }
            },
        )
        response.raise_for_status()
        response_json = response.json()
        site_id = response_json["credentials"]["site"]["id"]
        api_token = response_json["credentials"]["token"]
        return api_token, site_id
