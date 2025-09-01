import os
import requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

REPO_OWNER = "Manoj-Murari"
REPO_NAME = "aegis-test-repo"
PR_NUMBER = 1

# --- Gemini Configuration ---
GEMINI_MODEL = "gemini-1.5-flash"

def get_pr_diff(owner: str, repo: str, pr_number: int) -> str | None:
    """Fetches the diff of a specific GitHub pull request."""
    if not GITHUB_TOKEN:
        print("❌ ERROR: GITHUB_TOKEN not found in environment variables.")
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
    if not GITHUB_TOKEN:
        print("❌ ERROR: GITHUB_TOKEN not found in environment variables.")
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
    """
    Analyzes the code changes using the Gemini API and generates a review.

    Args:
        diff (str): The diff text from the pull request.

    Returns:
        str: The AI-generated review comment.
    """
    if not GEMINI_API_KEY:
        return "Cannot analyze code because GEMINI_API_KEY is not set."
        
    print(f"🧠 Analyzing diff with Gemini model: {GEMINI_MODEL}...")

    # Initialize the Gemini LLM, passing the API key directly
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY)

    # This is our first, simple engineered prompt
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
        # Get the response from the LLM
        response = llm.invoke(prompt_template)
        print("✅ AI analysis complete.")
        return response.content
    except Exception as e:
        print(f"❌ An error occurred during AI analysis: {e}")
        return "An error occurred while analyzing the code. Please check the logs."


if __name__ == "__main__":
    print("--- Running AI Pull Request Reviewer (Analysis Phase) ---")

    # Step 1: Read the diff from the pull request
    diff_content = get_pr_diff(REPO_OWNER, REPO_NAME, PR_NUMBER)

    if diff_content:
        # Step 2: Analyze the diff with our AI
        ai_review = analyze_code_changes(diff_content)

        # Step 3: Format the final comment
        final_comment = f"### 🤖 Aegis AI Review\n\n"
        final_comment += ai_review

        # Step 4: Post the AI-generated review to the PR
        success = post_comment_on_pr(REPO_OWNER, REPO_NAME, PR_NUMBER, final_comment)

        if success:
            print("\n--- AI Review complete. ---")
        else:
            print("\n--- Posting AI review failed. ---")
    else:
        print("\n--- Fetching diff failed. Cannot proceed with review. ---")

