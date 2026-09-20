#!/usr/bin/env python3
"""Safely copy one immutable Phase 108 checkpoint between two SSH hosts.

Dry-run is the default.  A transfer is only attempted with ``--execute`` and
refuses to replace an existing destination.  The source and destination are
SHA-256 verified after transfer; this utility never reads or modifies a
production adapter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import uuid
from pathlib import PurePosixPath


def _remote(host: str, command: str, *, input_data: bytes | None = None) -> bytes:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, command],
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def _sha256(host: str, path: PurePosixPath) -> str:
    output = _remote(host, f"shasum -a 256 -- {shlex.quote(str(path))}").decode()
    digest = output.split()[0]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError(f"unexpected SHA-256 response from {host}: {output!r}")
    return digest


def plan(source_host: str, destination_host: str, source: PurePosixPath, destination: PurePosixPath) -> dict[str, str]:
    source_hash = _sha256(source_host, source)
    exists = _remote(destination_host, f"[ ! -e {shlex.quote(str(destination))} ] && echo clear").decode().strip()
    if exists != "clear":
        raise FileExistsError(f"destination already exists: {destination_host}:{destination}")
    return {
        "source": f"{source_host}:{source}",
        "destination": f"{destination_host}:{destination}",
        "source_sha256": source_hash,
        "status": "ready_to_copy",
    }


def copy(source_host: str, destination_host: str, source: PurePosixPath, destination: PurePosixPath) -> str:
    destination_parent = destination.parent
    temporary = destination.with_name(f".{destination.name}.partial-{uuid.uuid4().hex}")
    _remote(destination_host, f"umask 077; mkdir -p -- {shlex.quote(str(destination_parent))}; chmod 700 -- {shlex.quote(str(destination_parent))}")
    source_bytes = _remote(source_host, f"cat -- {shlex.quote(str(source))}")
    try:
        _remote(destination_host, f"umask 077; cat > {shlex.quote(str(temporary))}; chmod 600 -- {shlex.quote(str(temporary))}", input_data=source_bytes)
        temporary_hash = _sha256(destination_host, temporary)
        source_hash = _sha256(source_host, source)
        if temporary_hash != source_hash:
            raise RuntimeError("hash mismatch before publishing transfer")
        _remote(destination_host, f"[ ! -e {shlex.quote(str(destination))} ] && mv -- {shlex.quote(str(temporary))} {shlex.quote(str(destination))}")
        return _sha256(destination_host, destination)
    finally:
        _remote(destination_host, f"rm -f -- {shlex.quote(str(temporary))}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-host", required=True)
    parser.add_argument("--destination-host", required=True)
    parser.add_argument("--source", type=PurePosixPath, required=True)
    parser.add_argument("--destination", type=PurePosixPath, required=True)
    parser.add_argument("--execute", action="store_true", help="perform transfer; otherwise only preflight")
    args = parser.parse_args()
    result = plan(args.source_host, args.destination_host, args.source, args.destination)
    if args.execute:
        result["destination_sha256"] = copy(args.source_host, args.destination_host, args.source, args.destination)
        if result["source_sha256"] != result["destination_sha256"]:
            raise RuntimeError("hash mismatch after transfer")
        result["status"] = "copied_and_verified"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
