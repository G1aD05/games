
import hashlib
import json
import mimetypes
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CHUNK_SIZE = 24 * 1024 * 1024
FILE_LIMIT = 25 * 1024 * 1024

CHUNK_DIR = "__chunks__"
MANIFEST_FILE = "__chunks_manifest.json"


def load_manifest():
    path = ROOT / MANIFEST_FILE

    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    return {}


def split_file(path, manifest):
    relative = path.relative_to(ROOT).as_posix()
    size = path.stat().st_size

    if size <= FILE_LIMIT:
        return False

    identifier = hashlib.sha256(
        relative.encode("utf-8")
    ).hexdigest()[:24]

    folder = ROOT / CHUNK_DIR / identifier
    folder.mkdir(parents=True, exist_ok=True)

    chunks = []

    print(f"\nSplitting {relative} ({size / 1048576:.2f} MB)")

    with path.open("rb") as source:
        index = 0

        while True:
            data = source.read(CHUNK_SIZE)

            if not data:
                break

            filename = f"{index:06d}.bin"
            destination = folder / filename

            with destination.open("wb") as output:
                output.write(data)

            chunks.append(
                f"/{CHUNK_DIR}/{identifier}/{filename}"
            )

            print(f"  Created {filename}: {len(data) / 1048576:.2f} MB")
            index += 1

    manifest[relative] = {
        "size": size,
        "type": (
            mimetypes.guess_type(path.name)[0]
            or "application/octet-stream"
        ),
        "chunks": chunks
    }

    return True


def main():
    manifest = load_manifest()

    files = [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and CHUNK_DIR not in path.relative_to(ROOT).parts
        and path.name not in {
            MANIFEST_FILE,
            "split_large_files.py"
        }
        and ".git" not in path.relative_to(ROOT).parts
    ]

    print(f"Scanning games directory: {ROOT}")
    print(f"Files found: {len(files)}")

    converted = []

    for path in files:
        if path.stat().st_size > FILE_LIMIT:
            if split_file(path, manifest):
                converted.append(path)

    if not converted:
        print("\nNo oversized files found.")
        return

    manifest_path = ROOT / MANIFEST_FILE
    temporary_path = ROOT / (MANIFEST_FILE + ".tmp")

    temporary_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    os.replace(temporary_path, manifest_path)

    # Only delete originals after manifest is safely written.
    for path in converted:
        path.unlink()
        print(f"Removed original: {path.relative_to(ROOT)}")

    print("\nSplitting complete!")
    print(f"Files split: {len(converted)}")
    print(f"Manifest: {MANIFEST_FILE}")
    print("\nYou can now commit and push the modified games directory.")


if __name__ == "__main__":
    main()

