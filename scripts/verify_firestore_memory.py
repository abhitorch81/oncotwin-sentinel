"""Two-process Firestore restart proof for a synthetic OncoTwin mission."""

import argparse
import json
import os
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from apps.api.app.memory import FirestoreMissionRepository
from apps.api.app.mission_service import MissionService


def repository() -> FirestoreMissionRepository:
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    if not project_id:
        raise SystemExit("GOOGLE_CLOUD_PROJECT is not configured")
    return FirestoreMissionRepository(
        project_id,
        database=os.environ.get("FIRESTORE_DATABASE", "(default)"),
    )


def write() -> None:
    store = repository()
    try:
        mission = MissionService(store).start(
            "Restart proof: investigate the synthetic resistant red clone"
        )
        print(json.dumps({
            "phase": "write",
            "mission_id": mission.id,
            "receipt_sha256_prefix": mission.receipt.receipt_sha256[:12],
            "state": mission.state,
        }))
    finally:
        store.close()


def read(mission_id: str) -> None:
    store = repository()
    try:
        mission = store.get(mission_id)
        if mission is None:
            raise SystemExit("Mission was not found after process restart")
        print(json.dumps({
            "phase": "read_after_restart",
            "mission_id": mission.id,
            "receipt_sha256_prefix": mission.receipt.receipt_sha256[:12],
            "state": mission.state,
            "persistent": True,
        }))
    finally:
        store.close()


def proof() -> None:
    store = repository()
    try:
        print(json.dumps(store.proof()))
    finally:
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("write")
    subparsers.add_parser("proof")
    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("mission_id")
    args = parser.parse_args()
    if args.command == "write":
        write()
    elif args.command == "read":
        read(args.mission_id)
    else:
        proof()


if __name__ == "__main__":
    main()
