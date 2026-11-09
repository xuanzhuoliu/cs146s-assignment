"""Record comparable, local snapshot metadata without executing repository code."""
import collections
import datetime
import json
import pathlib
import subprocess

week5 = pathlib.Path(__file__).resolve().parents[1]
study_root = week5.parents[1] / "study-repos"
records = []
for name in ("dayjs", "yt-dlp", "redis"):
    repo = study_root / name

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args]).decode().strip()

    entries = subprocess.check_output(
        ["git", "-C", str(repo), "ls-tree", "-r", "-l", "-z", "HEAD"]
    ).split(b"\0")
    extensions = collections.Counter()
    count = size = 0
    for entry in entries:
        if not entry:
            continue
        metadata, filename = entry.split(b"\t", 1)
        mode, kind, sha, length = metadata.split()
        if kind != b"blob":
            continue
        count += 1
        size += int(length)
        extensions[pathlib.PurePosixPath(filename.decode()).suffix or "[no extension]"] += 1
    records.append({
        "name": name,
        "origin": git("remote", "get-url", "origin"),
        "commit_sha": git("rev-parse", "HEAD"),
        "commit_date": git("show", "-s", "--format=%cI", "HEAD"),
        "branch": git("branch", "--show-current"),
        "shallow_clone": git("rev-parse", "--is-shallow-repository") == "true",
        "working_tree_status": git("status", "--porcelain"),
        "tracked_blob_count": count,
        "tracked_blob_bytes": size,
        "extension_file_counts": dict(extensions.most_common()),
    })
result = {
    "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "method": "git ls-tree HEAD: tracked blobs only; includes vendored/generated blobs; bytes are not SLOC. File extensions are not language byte shares. Shallow commit dates do not establish project age.",
    "factory_reports_generated": False,
    "repositories": records,
}
out = week5 / "evidence" / "repository-snapshots.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + "\n")
print(out)
