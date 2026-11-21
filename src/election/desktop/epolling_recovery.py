"""Persist only the authorization reference needed to resolve a voting session."""

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import UUID

from PySide6.QtCore import QLockFile

from election.private_paths import private_directory, private_file, private_file_descriptor


@dataclass(frozen=True)
class VotingSession:
    server_url: str
    station_id: int
    session_id: str


class VotingSessionJournal:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._pending = directory / "e-polling.pending"
        self._lock: QLockFile | None = None

    def exists(self) -> bool:
        try:
            self._pending.lstat()
        except FileNotFoundError:
            return False
        return True

    def acquire(self) -> bool:
        self._directory.mkdir(mode=0o700, exist_ok=True, parents=True)
        if not private_directory(self._directory):
            raise OSError("Voting session journal directory is not private")
        lock = QLockFile(str(self._pending.with_suffix(".lock")))
        # A process can stay in the private view for longer than Qt's default timeout.
        lock.setStaleLockTime(0)
        if not lock.tryLock(0):
            if lock.error() != QLockFile.LockError.LockFailedError:
                raise OSError("Voting session journal lock is unavailable")
            return False
        self._lock = lock
        return True

    def release(self) -> None:
        if self._lock is not None:
            self._lock.unlock()
            self._lock = None

    def read(self) -> VotingSession | None:
        if not self.exists():
            return None
        if not private_file(self._pending):
            raise OSError("Voting session journal is not private")
        try:
            data = json.loads(self._pending.read_text(encoding="utf-8"))
            if (
                isinstance(data, dict)
                and set(data) == {"server_url", "station_id", "session_id"}
                and isinstance(data["server_url"], str)
                and data["server_url"].startswith("https://")
                and type(data["station_id"]) is int
                and data["station_id"] > 0
                and isinstance(data["session_id"], str)
                and str(UUID(data["session_id"])) == data["session_id"]
            ):
                return VotingSession(data["server_url"], data["station_id"], data["session_id"])
        except (ValueError, RecursionError) as exc:
            raise OSError("Voting session journal is invalid") from exc
        raise OSError("Voting session journal is invalid")

    def write(self, session: VotingSession) -> None:
        descriptor, temporary = tempfile.mkstemp(prefix=".e-polling-", dir=self._directory)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                os.fchmod(output.fileno(), 0o600)
                if not private_file_descriptor(output.fileno()):
                    raise OSError("Voting session journal is not private")
                json.dump(asdict(session), output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self._pending)
            if os.name == "posix":
                # Persist the journal name before allowing a network submission.
                directory_fd = os.open(self._directory, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def clear(self) -> None:
        self._pending.unlink(missing_ok=True)
