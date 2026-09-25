import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.db import SessionDep
from app.core.rate_limit import allow
from app.modules.auth.deps import MemberDep
from app.modules.auth.github import GitHubError, GitHubHttpDep
from app.modules.repos import service
from app.modules.repos.schemas import MAX_REPOS, RepoAdd, RepoOut, RepoPage
from app.modules.users.deps import ProfileOwnerDep

router = APIRouter(tags=["repos"])

NOT_FOUND = "That repo isn't on Lantern Grid."


@router.post("/repos", operation_id="addRepo", status_code=status.HTTP_201_CREATED)
async def add_repo(data: RepoAdd, user: MemberDep, db: SessionDep, http: GitHubHttpDep) -> RepoOut:
    if not await allow(f"repo:{user.id}", limit=30, window_seconds=3600):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "That's a lot of repos for one hour. Try later."
        )
    try:
        return await service.add(db, http, user, data.repo)
    except service.BadRepoRefError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Paste a GitHub link or owner/name, like vercel/next.js.",
        ) from None
    except service.NotOnGitHubError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "GitHub doesn't have a public repo by that name."
        ) from None
    except service.DuplicateRepoError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "That repo is already on your profile."
        ) from None
    except service.TooManyReposError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"You can add up to {MAX_REPOS} repos."
        ) from None
    except GitHubError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "GitHub isn't answering right now. Try again soon."
        ) from None


@router.get("/repos/{repo_id}", operation_id="getRepo")
async def get_repo(repo_id: uuid.UUID, db: SessionDep) -> RepoOut:
    try:
        return service.to_out(await service.get(db, repo_id))
    except service.RepoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.delete(
    "/repos/{repo_id}",
    operation_id="deleteRepo",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_repo(repo_id: uuid.UUID, user: MemberDep, db: SessionDep) -> None:
    try:
        await service.remove(db, user, repo_id)
    except service.RepoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.get("/users/{username}/repos", operation_id="listUserRepos")
async def list_user_repos(
    owner: ProfileOwnerDep,
    db: SessionDep,
    cursor: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> RepoPage:
    return await service.by_owner(db, owner, cursor=cursor, limit=limit)
