#%%
#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Pull all PMWiki files from SFTP server.

Syncs the full remote PMWiki directory tree locally, downloading only
files that are new or modified since the last sync (by mtime/size).

Usage:
    python pull_wiki.py              # sync all files
    python pull_wiki.py --list       # list remote directories without downloading
"""

import os
import stat
import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv

load_dotenv()

# When running inside Jupyter/IPython, set this to True to list instead of sync
LIST_ONLY = False

SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_PORT = int(os.getenv("SFTP_PORT"))
SFTP_USERNAME = os.getenv("SFTP_USERNAME")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
REMOTE_BASE = os.getenv("SFTP_REMOTE_BASE")

LOCAL_BASE = Path(__file__).parent / "pmwiki_data"


def needs_update(entry, local_path):
    """Check if a remote file is newer or different size than the local copy."""
    if not local_path.exists():
        return True
    local_stat = local_path.stat()
    if entry.st_size != local_stat.st_size:
        return True
    if entry.st_mtime > local_stat.st_mtime:
        return True
    return False


def sync_dir(sftp, remote_dir, local_dir):
    """Recursively sync a remote directory, downloading only changed files."""
    local_dir.mkdir(parents=True, exist_ok=True)
    updated = 0
    skipped = 0

    try:
        entries = sftp.listdir_attr(str(remote_dir))
    except PermissionError:
        print(f"  [skip] no permission: {remote_dir}")
        return 0, 0

    for entry in entries:
        remote_path = f"{remote_dir}/{entry.filename}"
        local_path = local_dir / entry.filename

        if stat.S_ISDIR(entry.st_mode):
            u, s = sync_dir(sftp, remote_path, local_path)
            updated += u
            skipped += s
        else:
            if needs_update(entry, local_path):
                print(f"  updated: {remote_path}")
                try:
                    sftp.get(remote_path, str(local_path))
                    os.utime(local_path, (entry.st_atime, entry.st_mtime))
                    updated += 1
                except PermissionError:
                    print(f"  [skip] no permission: {remote_path}")
            else:
                skipped += 1

    return updated, skipped


def list_remote(sftp, remote_dir, indent=0):
    """List the remote directory tree."""
    try:
        entries = sftp.listdir_attr(str(remote_dir))
    except PermissionError:
        print(f"{'  ' * indent}[no permission]")
        return

    dirs = []
    files = 0
    for entry in entries:
        if stat.S_ISDIR(entry.st_mode):
            dirs.append(entry.filename)
        else:
            files += 1

    for d in sorted(dirs):
        print(f"{'  ' * indent}{d}/")
        list_remote(sftp, f"{remote_dir}/{d}", indent + 1)
    if files:
        print(f"{'  ' * indent}({files} files)")


def connect():
    """Establish SFTP connection."""
    if not SFTP_USERNAME or not SFTP_PASSWORD:
        print("Error: SFTP_USERNAME and SFTP_PASSWORD must be set in .env")
        sys.exit(1)

    print(f"Connecting to {SFTP_HOST}:{SFTP_PORT} as {SFTP_USERNAME}...")
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return transport, sftp


def main():
    # When run from terminal, --list flag overrides LIST_ONLY variable
    in_jupyter = "ipykernel" in sys.argv[0] if sys.argv else False
    do_list = LIST_ONLY if in_jupyter else ("--list" in sys.argv)

    transport, sftp = connect()

    try:
        if do_list:
            print(f"\nRemote directory tree ({REMOTE_BASE}):\n")
            list_remote(sftp, REMOTE_BASE)
        else:
            print(f"\nSyncing {REMOTE_BASE} -> {LOCAL_BASE}\n")
            updated, skipped = sync_dir(sftp, REMOTE_BASE, LOCAL_BASE)
            print(f"\n  -> {updated} updated, {skipped} unchanged")
    finally:
        sftp.close()
        transport.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
