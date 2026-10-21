"""
FastAPI Main Application for CodeSentinel AI Code Review Platform.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure local backend imports resolve properly
sys.path.append(str(Path(__file__).parent))

from analyzer import CodeAnalyzer
from github_client import GitHubClient
from samples import SAMPLES, get_sample_by_id

app = FastAPI(
    title="CodeSentinel AI - Code Review Platform",
    description="Enterprise-grade AI-powered code & PR review platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Models -----------------

class ReviewRequest(BaseModel):
    code: str
    file_path: Optional[str] = "main.py"
    language: Optional[str] = "python"
    strictness: Optional[str] = "standard"  # relaxed, standard, paranoid
    focus_areas: Optional[List[str]] = ["security", "performance", "architecture", "style"]
    provider: Optional[str] = "auto"        # auto, gemini, openai, heuristic
    api_key: Optional[str] = None
    model: Optional[str] = None

class GitHubReviewRequest(BaseModel):
    pr_url: str
    github_token: Optional[str] = None
    provider: Optional[str] = "auto"
    api_key: Optional[str] = None
    model: Optional[str] = None
    strictness: Optional[str] = "standard"

class PostGitHubReviewRequest(BaseModel):
    pr_url: str
    github_token: str
    event: str = "COMMENT"  # APPROVE, REQUEST_CHANGES, COMMENT
    body: str

# ----------------- API Endpoints -----------------

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "CodeSentinel AI",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "github_token_configured": bool(os.getenv("GITHUB_TOKEN")),
    }

@app.get("/api/samples")
def get_samples():
    """Returns list of interactive demo scenarios."""
    return SAMPLES

@app.post("/api/review")
def review_code(req: ReviewRequest):
    """Reviews any code snippet or unified diff directly."""
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Code content cannot be empty.")
        
    analyzer = CodeAnalyzer(api_key=req.api_key, provider=req.provider, model=req.model)
    result = analyzer.analyze(
        code_or_diff=req.code,
        file_path=req.file_path or "code.py",
        strictness=req.strictness or "standard",
        focus_areas=req.focus_areas
    )
    return result

@app.post("/api/review/github")
def review_github_pr(req: GitHubReviewRequest):
    """Fetches a Pull Request from GitHub and conducts an automated review."""
    parsed = GitHubClient.parse_pr_url(req.pr_url)
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub PR URL. Expected format: https://github.com/:owner/:repo/pull/:pr_number"
        )
    owner, repo, pr_number = parsed

    token = req.github_token or os.getenv("GITHUB_TOKEN")
    client = GitHubClient(token=token)

    try:
        pr_data = client.fetch_pr_data(owner, repo, pr_number)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Review the PR's unified diff or patches
    content_to_review = pr_data.get("diff")
    if not content_to_review and pr_data.get("files"):
        content_to_review = "\n\n".join(
            f"--- {f['filename']}\n+++ {f['filename']}\n{f.get('patch', '')}"
            for f in pr_data["files"]
        )

    if not content_to_review:
        content_to_review = "# No code changes found in this pull request."

    analyzer = CodeAnalyzer(api_key=req.api_key, provider=req.provider, model=req.model)
    analysis = analyzer.analyze(
        code_or_diff=content_to_review,
        file_path=f"PR #{pr_number} ({owner}/{repo})",
        strictness=req.strictness or "standard"
    )

    return {
        "pr_info": pr_data,
        "review": analysis
    }

@app.post("/api/github/post-review")
def post_github_review(req: PostGitHubReviewRequest):
    """Posts a completed review comment back to GitHub PR."""
    parsed = GitHubClient.parse_pr_url(req.pr_url)
    if not parsed:
        raise HTTPException(status_code=400, detail="Invalid GitHub PR URL.")
    owner, repo, pr_number = parsed

    client = GitHubClient(token=req.github_token)
    try:
        res = client.post_review(owner, repo, pr_number, req.event, req.body)
        return {"success": True, "github_response": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- Frontend Static Serving -----------------

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def serve_index():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "CodeSentinel API is running. Frontend index.html not found."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
