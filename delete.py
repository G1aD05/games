import argparse
import json
import re
import shutil
import urllib.request
from pathlib import Path

REPO = "G1aD05/games"
BRANCH = "upload"


def normalize(name):
    name = name.lower()
    name = re.sub(r"-unblocked$", "", name)
    return re.sub(r"[^a-z0-9]", "", name)


def get_remote_games():
    url = (
        f"https://api.github.com/repos/{REPO}"
        f"/git/trees/{BRANCH}?recursive=1"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Game-Deduplicator"}
    )

    with urllib.request.urlopen(request) as response:
        data = json.load(response)

    if data.get("truncated"):
        raise RuntimeError("GitHub returned a truncated repository tree.")

    return {
        normalize(item["path"].split("/")[-1])
        for item in data["tree"]
        if item["type"] == "tree"
        and "/" not in item["path"]
    }


def main():
    parser = argparse.ArgumentParser(
        description="Remove local games already present on GitHub."
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing your local game folders."
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete matching folders."
    )

    args = parser.parse_args()

    root = Path(args.directory).expanduser().resolve()

    if not root.is_dir():
        raise SystemExit(f"Directory does not exist: {root}")

    print("Fetching GitHub game list...")
    remote_games = get_remote_games()

    matches = []

    for folder in root.iterdir():
        if not folder.is_dir() or folder.is_symlink():
            continue

        if normalize(folder.name) in remote_games:
            matches.append(folder)

    print(f"\nLocal directory: {root}")
    print(f"Remote game folders: {len(remote_games)}")
    print(f"Matching local games: {len(matches)}")

    if not matches:
        print("\nNothing to remove.")
        return

    print("\nMatching games:")

    for folder in matches:
        print(f"  {folder.name}")

    if not args.delete:
        print("\nDRY RUN: Nothing was deleted.")
        print("Run again with --delete to remove these folders.")
        return

    confirm = input(
        f"\nPermanently delete {len(matches)} game folders? (yes/no): "
    )

    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    for folder in matches:
        shutil.rmtree(folder)
        print(f"Deleted: {folder.name}")

    print(f"\nFinished. Deleted {len(matches)} game folders.")


if __name__ == "__main__":
    main()
