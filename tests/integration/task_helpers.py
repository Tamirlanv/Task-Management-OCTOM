from dataclasses import dataclass

from httpx import AsyncClient

from tests.integration.helpers import Identity, account, member, workspace


@dataclass(frozen=True)
class Board:
    owner: Identity
    member: Identity
    viewer: Identity
    workspace_id: str
    project_id: str
    tag_id: str

    @property
    def base(self) -> str:
        return f"/api/v1/workspaces/{self.workspace_id}"

    @property
    def tasks(self) -> str:
        return f"{self.base}/projects/{self.project_id}/tasks"


async def board(client: AsyncClient) -> Board:
    owner = await account(client, "owner")
    teammate = await account(client, "teammate")
    viewer = await account(client, "viewer")
    workspace_id = await workspace(client, owner)
    await member(client, workspace_id, owner, teammate, "Member")
    await member(client, workspace_id, owner, viewer, "Viewer")
    base = f"/api/v1/workspaces/{workspace_id}"
    project = await client.post(
        f"{base}/projects", headers=owner.headers, json={"name": "Project"}
    )
    tag = await client.post(
        f"{base}/tags", headers=owner.headers, json={"name": "Backend"}
    )
    assert project.status_code == tag.status_code == 201
    return Board(
        owner, teammate, viewer, workspace_id, project.json()["id"], tag.json()["id"]
    )
