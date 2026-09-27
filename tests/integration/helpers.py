from dataclasses import dataclass

from httpx import AsyncClient


@dataclass(frozen=True)
class Identity:
    id: str
    email: str
    headers: dict[str, str]


async def account(client: AsyncClient, name: str) -> Identity:
    email = f"{name}@example.com"
    password = "test-password-at-least-twelve"
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text
    return Identity(
        response.json()["id"],
        email,
        {"Authorization": f"Bearer {login.json()['access_token']}"},
    )


async def workspace(client: AsyncClient, owner: Identity, name: str = "Team") -> str:
    response = await client.post(
        "/api/v1/workspaces", headers=owner.headers, json={"name": name}
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


async def member(
    client: AsyncClient, workspace_id: str, owner: Identity, target: Identity, role: str
) -> None:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=owner.headers,
        json={"email": target.email, "role": role},
    )
    assert response.status_code == 201, response.text
