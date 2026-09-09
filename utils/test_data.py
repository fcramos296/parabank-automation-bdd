from dataclasses import dataclass
from uuid import uuid4


DEFAULT_PASSWORD = "Password123!"


@dataclass(frozen=True, slots=True)
class CustomerData:
    first_name: str
    last_name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    ssn: str
    username: str
    password: str

    def ui_data(self) -> dict[str, str]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "phone": self.phone,
            "ssn": self.ssn,
            "username": self.username,
            "password": self.password,
            "confirm_password": self.password,
        }

    def registration_payload(self) -> dict[str, str]:
        return {
            "customer.firstName": self.first_name,
            "customer.lastName": self.last_name,
            "customer.address.street": self.address,
            "customer.address.city": self.city,
            "customer.address.state": self.state,
            "customer.address.zipCode": self.zip_code,
            "customer.phoneNumber": self.phone,
            "customer.ssn": self.ssn,
            "customer.username": self.username,
            "customer.password": self.password,
            "repeatedPassword": self.password,
        }


def unique_username(
    prefix: str = "qa",
) -> str:
    safe_prefix = "".join(
        char
        for char in prefix.lower()
        if char.isalnum()
    )[:8] or "qa"

    return f"{safe_prefix}_{uuid4().hex[:10]}"


def unique_ssn() -> str:
    number = int(uuid4().hex[:12], 16)

    return str(
        number % 1_000_000_000
    ).zfill(9)


def build_customer(
    prefix: str = "qa",
    *,
    username: str | None = None,
    password: str = DEFAULT_PASSWORD,
) -> CustomerData:
    return CustomerData(
        first_name="QA",
        last_name="Automation",
        address="Av. Paulista 1000",
        city="Sao Paulo",
        state="SP",
        zip_code="01310-100",
        phone="11999999999",
        ssn=unique_ssn(),
        username=username or unique_username(prefix),
        password=password,
    )