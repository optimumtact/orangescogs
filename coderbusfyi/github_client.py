from __future__ import annotations

import base64

import aiohttp


class GitHubResourcesClient:
    def __init__(
        self,
        bot,
        config,
        default_repo_owner,
        default_repo_name,
        default_branch,
        default_resource_path,
    ):
        self.bot = bot
        self.config = config
        self.default_repo_owner = default_repo_owner
        self.default_repo_name = default_repo_name
        self.default_branch = default_branch
        self.default_resource_path = default_resource_path

    async def get_token(self):
        return await self.config.github_token()

    async def get_repo_details(self):
        owner = await self.config.repo_owner() or self.default_repo_owner
        name = await self.config.repo_name() or self.default_repo_name
        branch = await self.config.default_branch() or self.default_branch
        path = await self.config.resource_path() or self.default_resource_path
        return owner, name, branch, path

    async def require_token(self, interaction):
        token = await self.get_token()
        if not token:
            await interaction.response.send_message(
                "GitHub API token is not configured. Use /setgithubkey first.",
                ephemeral=True,
            )
            return None
        return token

    async def fetch_remote_resources(self):
        token = await self.get_token()
        if token is None:
            return None, None, None

        owner, name, branch, path = await self.get_repo_details()
        url = (
            f"https://api.github.com/repos/{owner}/{name}/contents/{path}?ref={branch}"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub request failed: {response.status} {text}"
                    )
                data = await response.json()
                content = data.get("content", "")
                content = base64.b64decode(content).decode("utf-8")
                return content, data.get("sha"), path

    async def write_remote_resources(self, new_contents):
        token = await self.get_token()
        if not token:
            raise RuntimeError("No GitHub API token is configured.")

        owner, name, branch, path = await self.get_repo_details()
        url = f"https://api.github.com/repos/{owner}/{name}/contents/{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        _, sha, _ = await self.fetch_remote_resources()
        payload = {
            "message": "Update CoderBusFYI resources.ini",
            "branch": branch,
            "content": base64.b64encode(new_contents.encode("utf-8")).decode("utf-8"),
            "sha": sha,
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload, headers=headers) as response:
                if response.status not in (200, 201):
                    text = await response.text()
                    raise RuntimeError(f"GitHub write failed: {response.status} {text}")
                return await response.json()

    async def load_resources(self):
        content, _, _ = await self.fetch_remote_resources()
        if content is None:
            return ""
        return content

    async def save_resources(self, text):
        return await self.write_remote_resources(text)
