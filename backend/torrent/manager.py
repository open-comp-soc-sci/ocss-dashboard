#!/usr/bin/env python3
import sys
import os
import subprocess
import threading
import time

def stream_output(proc, name):
    """Reads lines from proc.stdout and prints them, tagged by chunk name."""
    for line in proc.stdout:
        print(f"[{name}] {line}", end="")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/bigfile.jsonl[.zst] [num_chunks]")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    # If the file is a .zst, decompress it first.
    was_zst = False
    if file_path.endswith(".zst"):
        was_zst = True
        print(f"Decompressing {file_path}...")
        # Example: "zstd -d RC_2024-05.zst" -> produces "RC_2024-05"
        subprocess.run(["zstd", "-d", file_path], check=True)

        # The unzipped file is the original filename minus ".zst"
        unzipped_path = file_path[:-4]
        if not os.path.isfile(unzipped_path):
            print(f"Error: decompressed file not found: {unzipped_path}")
            sys.exit(1)

        # Update file_path so the rest of the logic sees the unzipped file
        file_path = unzipped_path

    # Number of chunks to split into (default: 16)
    num_chunks = 16
    if len(sys.argv) >= 3:
        num_chunks = int(sys.argv[2])

    # 1. Create a prefix for chunk files
    prefix = os.path.basename(file_path) + "_chunk_"

    # 2. Run 'split' to divide the file into 'num_chunks' line-based parts
    print(f"Splitting {file_path} into {num_chunks} chunks (line-based)...")
    cmd = [
        "split",
        "-n", f"l/{num_chunks}",  # line-based splitting into N chunks
        file_path,
        prefix
    ]
    subprocess.run(cmd, check=True)

    # 3. Find all chunk files
    chunk_files = []
    for fname in os.listdir("."):
        if fname.startswith(prefix):
            chunk_files.append(fname)
    chunk_files.sort()

    print(f"Created {len(chunk_files)} chunk files. Now spawning parallel ingestion...")

    # 4. Spawn multiple ingestion processes
    procs = []
    threads = []
    for chunk in chunk_files:
        # Pipe stdout so we can read from it
        p = subprocess.Popen(
            ["python", "-u", "insert_data.py", chunk],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        t = threading.Thread(target=stream_output, args=(p, chunk))
        t.start()
        procs.append(p)
        threads.append(t)

    # Periodically check done status
    while True:
        done_count = sum(1 for p in procs if p.poll() is not None)
        print(f"{done_count}/{len(procs)} chunks finished.")
        if done_count == len(procs):
            break
        time.sleep(10)

    # Wait for all threads to exit (so we consume all output)
    for t in threads:
        t.join()

    # Check exit codes
    exit_codes = [p.wait() for p in procs]
    if any(code != 0 for code in exit_codes):
        print("Some ingestion processes failed. Keeping chunk files for debugging.")
        sys.exit(1)
    else:
        print("All chunk ingestion processes completed successfully!")
        print("Deleting chunk files...")
        for chunk_file in chunk_files:
            os.remove(chunk_file)
        print("All chunk files deleted.")

    # If we decompressed a .zst file, remove the unzipped file now
    if was_zst:
        print(f"Removing unzipped file {file_path}...")
        os.remove(file_path)
        print("Unzipped file removed.")

if __name__ == "__main__":
    main()
