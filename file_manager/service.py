"""Business logic for workspace file management."""

from file_manager import backend
from file_manager.schemas import DirectoryListing, FileEntry


class FileManagerService:
    """Single service layer shared by REST, elFinder, and agent tools."""

    def list_directory(self, path: str = "") -> dict:
        entries = backend.list_directory(path)
        return DirectoryListing(
            path=path.replace("\\", "/"),
            entries=[FileEntry(**entry) for entry in entries],
        ).model_dump()

    def directory_tree(self, path: str = "") -> dict:
        return backend.directory_tree(path)

    def read_file(self, path: str) -> dict:
        return backend.read_file(path)

    def write_file(self, path: str, content: str) -> dict:
        return backend.write_file(path, content)

    def create(self, path: str, kind: str = "file") -> dict:
        return backend.create_path(path, kind)

    def delete(self, path: str) -> dict:
        return backend.delete_path(path)

    def move(self, source_path: str, destination_path: str) -> dict:
        return backend.move_path(source_path, destination_path)

    def copy(self, source_path: str, destination_path: str) -> dict:
        return backend.copy_path(source_path, destination_path)


file_manager_service = FileManagerService()
