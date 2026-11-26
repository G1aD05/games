import os
import subprocess
from pathlib import Path

BRANCH = "upload"
REMOTE = "origin"

# Maximum size of each batch: 90 MiB
BATCH_SIZE = 90 * 1024 * 1024

# Maximum number of files per batch
MAX_FILES = 50

GITHUB_FILE_LIMIT = 100 * 1024 * 1024


def git(*args, check=True):
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True
    )

    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    return result


def get_files():
    result = git(
        "ls-files",
        "-co",
        "--exclude-standard",
        "-z"
    )

    files = []

    for name in result.stdout.split("\0"):
        if not name:
            continue

        path = Path(name)

        if path.is_file():
            files.append((name, path.stat().st_size))

    return sorted(files)


def create_batches(files):
    batches = []
    current_batch = []
    current_size = 0

    for name, size in files:
        if size >= GITHUB_FILE_LIMIT:
            raise RuntimeError(
                f"File exceeds GitHub's 100 MB limit: {name} "
                f"({size / 1024 / 1024:.1f} MB)"
            )

        if current_batch and (
            current_size + size > BATCH_SIZE
            or len(current_batch) >= MAX_FILES
        ):
            batches.append(current_batch)
            current_batch = []
            current_size = 0

        current_batch.append(name)
        current_size += size

    if current_batch:
        batches.append(current_batch)

    return batches


def main():
    root = git("rev-parse", "--show-toplevel").stdout.strip()
    os.chdir(root)

    branch = git("branch", "--show-current").stdout.strip()

    if branch != BRANCH:
        raise RuntimeError(
            f"You are on branch '{branch}', not '{BRANCH}'.\n"
            f"Run: git switch {BRANCH}"
        )

    # Don't accidentally include unrelated staged changes.
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        raise RuntimeError(
            "You have staged changes. Commit or unstage them first."
        )

    # Make sure the remote exists.
    if not git("remote", "get-url", REMOTE, check=False).stdout.strip():
        raise RuntimeError(f"Git remote '{REMOTE}' is not configured.")

    files = get_files()

    if not files:
        print("No files found to upload.")
        return

    batches = create_batches(files)

    total_size = sum(size for _, size in files)

    print(f"Repository: {root}")
    print(f"Branch: {BRANCH}")
    print(f"Files: {len(files)}")
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
    print(f"Batches: {len(batches)}")

    print("\nBatch overview:")

    for i, batch in enumerate(batches, 1):
        size = sum(
            Path(name).stat().st_size
            for name in batch
        )

        print(
            f"  Batch {i}: {len(batch)} files, "
            f"{size / 1024 / 1024:.1f} MB"
        )

    answer = input("\nStart uploading? (yes/no): ")

    if answer.lower() != "yes":
        print("Cancelled.")
        return

    for i, batch in enumerate(batches, 1):
        print(f"\n{'=' * 50}")
        print(f"Uploading batch {i}/{len(batches)}")
        print(f"{'=' * 50}")

        git("add", "--", *batch)

        # Nothing to commit if these files are already committed.
        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            print("No changes in this batch. Skipping.")
            continue

        git(
            "commit",
            "-m",
            f"Upload game files (batch {i}/{len(batches)})"
        )

        print("Pushing to GitHub...")

        result = git(
            "push",
            "-u",
            REMOTE,
            BRANCH,
            check=False
        )

        if result.returncode != 0:
            print("\nUPLOAD FAILED!")
            print(result.stderr)
            print(
                "\nFix the issue and run this script again. "
                "Previously pushed batches will remain on GitHub."
            )
            return

        print(f"Batch {i} successfully pushed!")

    print("\nAll batches uploaded successfully!")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as error:
        print(f"\nERROR: {error}")
