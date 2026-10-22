"""Request and response schemas for workspace file operations."""

from typing import Literal

from pydantic import BaseModel, Field


class PathRequest(BaseModel):
    path: str = Field(..., min_length=1)


class FileContentRequest(PathRequest):
    content: str


class CreateRequest(PathRequest):
    kind: str = Field(default="file", pattern="^(file|directory)$")


class MoveRequest(BaseModel):
    source_path: str = Field(..., min_length=1)
    destination_path: str = Field(..., min_length=1)


class SelectRootRequest(BaseModel):
    path: str = Field(..., min_length=1)


class ManageRootsRequest(BaseModel):
    action: Literal["add", "remove"]
    paths: list[str] = Field(..., min_length=1)


class FileEntry(BaseModel):
    name: str
    path: str
    type: str
    size: int
    modified: float


class DirectoryListing(BaseModel):
    path: str
    entries: list[FileEntry]
