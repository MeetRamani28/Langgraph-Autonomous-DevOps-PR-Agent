import re
import logging

logger = logging.getLogger("JiraTool")

MOCK_JIRA_TICKETS = {
    "DEV-101": "1. User authentication must use parameterized queries or ORM to prevent SQL Injection.\n2. No API keys or secrets may be hardcoded in the source code.\n3. Passwords must be hashed using bcrypt or Argon2.",
    "DEV-102": "1. All public REST API endpoints must enforce rate-limiting.\n2. Must return structured JSON error responses.",
    "DEFAULT": "1. Follow organizational clean code standards.\n2. Ensure zero critical security vulnerabilities.\n3. No plain-text secrets or credentials."
}


async def fetch_jira_requirements(branch_name: str, pr_title: str) -> str:
    """
    Extracts a Jira Ticket ID (e.g. DEV-101) from the branch name or PR title
    and returns the corresponding acceptance criteria.
    """
    logger.info(f"Looking up acceptance criteria for branch: '{branch_name}' / title: '{pr_title}'")
    
    match = re.search(r"([A-Z]+-\d+)", f"{branch_name} {pr_title}", re.IGNORECASE)
    
    if match:
        ticket_id = match.group(1).upper()
        requirements = MOCK_JIRA_TICKETS.get(ticket_id, MOCK_JIRA_TICKETS["DEFAULT"])
        logger.info(f"Found requirements for ticket [{ticket_id}].")
        return f"[Jira Ticket: {ticket_id}]\n{requirements}"
    
    logger.info("No explicit Jira ticket ID found. Returning DEFAULT security acceptance criteria.")
    return f"[Standard Security Policy]\n{MOCK_JIRA_TICKETS['DEFAULT']}"