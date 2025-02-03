import libtorrent as lt
import time
import os
from yaspin import yaspin

# Magnet link for downloading
MAGNET_LINK = "magnet:?xt=urn:btih:56aa49f9653ba545f48df2e33679f014d2829c10"

# Set up libtorrent session
ses = lt.session()
ses.listen_on(6881, 6891)

# Configure download parameters
params = {
    "save_path": "./downloads",  # Download directory inside the container
    "storage_mode": lt.storage_mode_t.storage_mode_sparse,
}

# Add the torrent
handle = lt.add_magnet_uri(ses, MAGNET_LINK, params)

print("Downloading metadata...")

# Wait until metadata is retrieved
while not handle.has_metadata():
    time.sleep(1)

print("Metadata retrieved, starting download...")

# Create a spinner for real-time progress updates
with yaspin(text="Downloading torrent...", color="cyan") as spinner:
    while not handle.is_seed():
        s = handle.status()
        spinner.text = f"Progress: {s.progress * 100:.2f}% | Downloaded: {s.total_download} bytes"
        time.sleep(5)  # Update every 5 seconds

print("\n✅ Download complete! Files saved in ./downloads")
