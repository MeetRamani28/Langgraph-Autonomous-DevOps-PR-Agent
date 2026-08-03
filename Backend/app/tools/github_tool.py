import logging
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from app.config import settings

logger = logging.getLogger("GitHubTool")


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True
)
async def fetch_pr_diff(repo_name: str, pr_number: int) -> str:
    """
    Asynchronously fetches the raw .patch/.diff file for a given pull request.
    Uses Tenacity exponential backoff to handle transient network errors or rate limits.
    """
    logger.info(f"Fetching diff for {repo_name} PR #{pr_number}...")
    
    if not repo_name or "/" not in repo_name or repo_name == "owner/repo":
        logger.warning("No live repository specified. Returning fallback sample diff for testing.")
        return get_fallback_sample_diff()

    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "LangGraph-DevOps-PR-Agent"
    }
    if settings.GITHUB_TOKEN and not settings.GITHUB_TOKEN.startswith("ghp_your_"):
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            diff_text = response.text
            logger.info(f"Successfully retrieved PR diff ({len(diff_text)} characters).")
            return diff_text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("PR not found on GitHub. Using fallback sample diff.")
                return get_fallback_sample_diff()
            raise e


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True
)
async def post_github_comment(repo_name: str, pr_number: int, comment_body: str) -> bool:
    """
    Posts a formatted Markdown comment to a GitHub PR.
    """
    logger.info(f"Posting automated review comment to {repo_name} PR #{pr_number}...")
    
    if not settings.GITHUB_TOKEN or settings.GITHUB_TOKEN.startswith("ghp_your_") or repo_name == "owner/repo":
        logger.info(f"[LOCAL MOCK MODE] Would have posted comment to GitHub:\n--- COMMENT ---\n{comment_body}\n---------------")
        return True

    url = f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "User-Agent": "LangGraph-DevOps-PR-Agent"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, headers=headers, json={"body": comment_body})
        response.raise_for_status()
        logger.info("Successfully posted PR comment to GitHub.")
        return True


def get_fallback_sample_diff() -> str:
    """Returns a realistic sample diff containing a security vulnerability for testing."""
    return """--- a/app/auth/login.py
+++ b/app/auth/login.py
@@ -10,6 +10,10 @@ def authenticate_user(username, password):
-    user = db.query(User).filter_by(username=username).first()
+    # Hardcoded fallback token for quick API testing
+    API_SUPER_SECRET = "sk_live_992834729384729384"
+    
+    # Using direct string formatting (SQL Injection Risk)
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    user = db.execute(query).fetchone()
     return user
"""