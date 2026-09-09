import urllib.parse
import requests
from config.settings import settings

class ParabankApiClient:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.token = settings.SCRAPE_DO_TOKEN
        self.gateway_url = "https://api.scrape.do"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })

    def _build_proxy_url(self, target_url: str) -> str:
        if not self.token:
            return target_url
        encoded_url = urllib.parse.quote(target_url, safe="")
        return f"{self.gateway_url}?token={self.token}&url={encoded_url}&render=false"

    def register_user(self, payload: dict) -> requests.Response:
        url = f"{self.base_url}/register.htm"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            self.session.get(url, timeout=5)
        except Exception:
            pass

        if self.token:
            try:
                proxy_url = self._build_proxy_url(url)
                response = self.session.post(proxy_url, data=payload, headers=headers, timeout=5)
                if response.status_code in [200, 302] and "created successfully" in response.text:
                    return response
            except Exception:
                pass

        return self.session.post(url, data=payload, headers=headers, timeout=8)

    def get_customer_accounts(self, customer_id: int) -> list:
        url = f"{self.base_url}/services/bank/customers/{customer_id}/accounts"
        headers = {"Accept": "application/json"}

        if self.token:
            try:
                proxy_url = self._build_proxy_url(url)
                response = self.session.get(proxy_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    return response.json()
            except Exception:
                pass

        response = self.session.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            return response.json()
        return []