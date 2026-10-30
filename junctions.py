"""Windows directory junctions, created without a shell or administrator rights."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import os
from pathlib import Path
import stat
import struct


class BranchError(ValueError):
    """A source or destination cannot safely be used."""


@dataclass(frozen=True)
class BranchStatus:
    label: str
    ready: bool = False
    linked: bool = False


def _local_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise BranchError("Choose a full folder path, including its drive letter.")
    if str(path).startswith("\\\\"):
        raise BranchError("Junctions need local drives. Network paths are not supported.")
    return path


def source_path(value: str | Path) -> Path:
    path = _local_path(value)
    if not path.is_dir():
        raise BranchError("The source folder does not exist.")
    path = path.resolve(strict=True)
    if not path.name:
        raise BranchError("Choose a source folder rather than a whole drive.")
    if str(path).startswith("\\\\"):
        raise BranchError("The source must be on a local drive.")
    return path


def is_junction(path: Path) -> bool:
    try:
        return path.lstat().st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT
    except (OSError, AttributeError):
        return False


def inspect_destination(source: str | Path, destination: str | Path) -> BranchStatus:
    try:
        original = source_path(source)
        branch = _local_path(destination)
        if branch.name in ("", ".", "..") or branch.is_reserved():
            raise BranchError("Choose a valid name for the branch folder.")
        if not branch.parent.is_dir():
            raise BranchError("The destination's parent folder does not exist.")

        # Resolve parent junctions as well, so indirect links cannot create a loop.
        branch = branch.parent.resolve(strict=True) / branch.name
        if original == branch or branch.is_relative_to(original) or original.is_relative_to(branch):
            raise BranchError("A branch cannot be inside its source, or contain its source.")

        if os.path.lexists(branch):
            if is_junction(branch):
                try:
                    if branch.resolve(strict=True) == original:
                        return BranchStatus("Already linked", linked=True)
                except OSError:
                    pass
                return BranchStatus("Blocked: junction points elsewhere")
            return BranchStatus("Blocked: destination already exists")
        return BranchStatus("Ready", ready=True)
    except (OSError, ValueError) as error:
        return BranchStatus(str(error))


def _set_junction(branch: Path, original: Path) -> None:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID,
                                      wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                                      ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
    kernel.DeviceIoControl.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL

    substitute_name = ("\\??\\" + str(original)).encode("utf-16-le")
    print_name = str(original).encode("utf-16-le")
    names = substitute_name + b"\0\0" + print_name + b"\0\0"
    # REPARSE_DATA_BUFFER header followed by its mount-point offsets and names.
    payload = struct.pack("<LHHHHHH", stat.IO_REPARSE_TAG_MOUNT_POINT, 8 + len(names), 0,
                          0, len(substitute_name), len(substitute_name) + 2, len(print_name)) + names
    buffer = ctypes.create_string_buffer(payload)
    handle = kernel.CreateFileW(str(branch), 0x40000000, 0x7, None, 3, 0x02200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        returned_bytes = wintypes.DWORD()
        if not kernel.DeviceIoControl(handle, 0x000900A4, buffer, len(payload), None, 0,
                                      ctypes.byref(returned_bytes), None):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)


def create_branch(source: str | Path, destination: str | Path) -> BranchStatus:
    if os.name != "nt":
        raise BranchError("Resource Brancher creates Windows junctions and needs Windows.")
    status = inspect_destination(source, destination)
    if status.linked:
        return status
    if not status.ready:
        raise BranchError(status.label)

    original = source_path(source)
    requested = _local_path(destination)
    branch = requested.parent.resolve(strict=True) / requested.name
    # mkdir fails if anything appeared here after validation. Never replace it.
    branch.mkdir()
    try:
        _set_junction(branch, original)
    except Exception:
        # Only remove the empty directory we just created. Never recurse.
        if branch.is_dir() and not is_junction(branch):
            branch.rmdir()
        raise
    return BranchStatus("Created", linked=True)
