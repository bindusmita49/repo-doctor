import os
import re
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import ClientSession

def _get_server_params() -> StdioServerParameters:
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise EnvironmentError("GITHUB_TOKEN is not set in your .env file.")
        
    return StdioServerParameters(
        command="npx.cmd",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": github_token}
    )

async def list_repo_files(owner: str, repo: str, path: str = "") -> str:
    """Lists files in a GitHub repository directory.
    
    Args:
        owner: The owner of the repository (e.g., 'octocat').
        repo: The repository name (e.g., 'Hello-World').
        path: The path to list files for. Use an empty string for the root directory.
    """
    server_params = _get_server_params()
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_file_contents", 
                arguments={"owner": owner, "repo": repo, "path": path}
            )
            return result.content[0].text

async def get_scrubbed_file_contents(owner: str, repo: str, path: str) -> str:
    """Gets the contents of a file from a GitHub repository, with secrets scrubbed.
    
    Args:
        owner: The owner of the repository (e.g., 'octocat').
        repo: The repository name (e.g., 'Hello-World').
        path: The path to the file.
    """
    server_params = _get_server_params()
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_file_contents", 
                arguments={"owner": owner, "repo": repo, "path": path}
            )
            content = result.content[0].text
            
            # --- INTERNAL REGEX SCRUBBER ---
            # Redact obvious API keys, tokens, and secrets before they reach the agent
            
            # Match typical GitHub Personal Access Tokens (ghp_, github_pat_, etc.)
            content = re.sub(r'(ghp_[0-9a-zA-Z]{36})', '[REDACTED_GITHUB_TOKEN]', content)
            content = re.sub(r'(github_pat_[0-9a-zA-Z_]{82})', '[REDACTED_GITHUB_PAT]', content)
            
            # Match typical Google/GCP API Keys (AIza...)
            content = re.sub(r'(AIza[0-9A-Za-z-_]{35})', '[REDACTED_GOOGLE_API_KEY]', content)
            
            # Match generic bearer tokens or authorization headers that look like JWTs or long hex strings
            content = re.sub(r'(Bearer\s+[A-Za-z0-9\-\._~+\/]+=*)', 'Bearer [REDACTED_TOKEN]', content)
            
            return content

list_repo_files = FunctionTool(list_repo_files)
get_scrubbed_file_contents = FunctionTool(get_scrubbed_file_contents)
