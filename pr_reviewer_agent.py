import os
import requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# These are now read from environment variables set by the GitHub Action
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
PR_NUMBER = os.getenv("PR_NUMBER")

# --- Gemini Configuration ---
GEMINI_MODEL = "gemini-1.5-flash"

# --- !! NEW DEBUGGING BLOCK !! ---
print("--- Initializing AI Reviewer ---")
print(f"Repository: {REPO_OWNER}/{REPO_NAME}")
print(f"Pull Request #: {PR_NUMBER}")
if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN environment variable is not set!")
else:
    print("✅ GITHUB_TOKEN found.")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY environment variable is not set!")
else:
    print("✅ GEMINI_API_KEY found.")
# -----------------------------------


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str | None:
    """Fetches the diff of a specific GitHub pull request."""
    if not all([owner, repo, pr_number, GITHUB_TOKEN]):
        print("❌ Missing required info for fetching diff.")
        return None

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"✅ Successfully fetched diff for PR #{pr_number}.")
        return response.text
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error occurred while fetching diff: {http_err}")
        print(f"   Response body: {response.text}")
    except Exception as err:
        print(f"❌ An other error occurred while fetching diff: {err}")
    return None

def post_comment_on_pr(owner: str, repo: str, pr_number: int, comment_body: str) -> bool:
    """Posts a comment on a specific GitHub pull request."""
    if not all([owner, repo, pr_number, GITHUB_TOKEN]):
        print("❌ Missing required info for posting comment.")
        return False

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"body": comment_body}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"✅ Successfully posted AI review comment on PR #{pr_number}.")
        print(f"   View it here: {response.json().get('html_url')}")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error occurred while posting comment: {http_err}")
        print(f"   Response body: {response.text}")
    except Exception as err:
        print(f"❌ An other error occurred while posting comment: {err}")
    return False

def analyze_code_changes(diff: str) -> str:
    """Analyzes the code changes using the Gemini API and generates a review."""
    if not GEMINI_API_KEY:
        return "Cannot analyze code because GEMINI_API_KEY is not set."
        
    print(f"🧠 Analyzing diff with Gemini model: {GEMINI_MODEL}...")
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY)

    prompt_template = f"""
    You are an expert code reviewer. Your goal is to provide a brief, helpful summary of the changes in this pull request.
    Please analyze the following code diff and provide a high-level summary in a few bullet points.
    Code Diff:
    ```diff
    {diff}
    ```
    Your review:
    """
    try:
        response = llm.invoke(prompt_template)
        print("✅ AI analysis complete.")
        return response.content
    except Exception as e:
        print(f"❌ An error occurred during AI analysis: {e}")
        return "An error occurred while analyzing the code. Please check the logs."

def main():
    """Main execution function."""
    print("--- Running AI Pull Request Reviewer (Analysis Phase) ---")
    
    # The PR number needs to be an integer
    try:
        pr_number_int = int(PR_NUMBER)
    except (ValueError, TypeError):
        print(f"❌ Invalid PR_NUMBER: '{PR_NUMBER}'. Must be an integer.")
        return

    diff_content = get_pr_diff(REPO_OWNER, REPO_NAME, pr_number_int)

    if diff_content:
        ai_review = analyze_code_changes(diff_content)
        final_comment = f"### 🤖 Aegis AI Review\n\n{ai_review}"
        
        success = post_comment_on_pr(REPO_OWNER, REPO_NAME, pr_number_int, final_comment)

        if success:
            print("\n--- AI Review complete. ---")
        else:
            print("\n--- Posting AI review failed. ---")
    else:
        print("\n--- Fetching diff failed. Cannot proceed with review. ---")


if __name__ == "__main__":
    main()

