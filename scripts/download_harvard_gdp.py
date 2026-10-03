"""Harvard-GDP RNFLT Stream Downloader.

Streams and extracts the 1,000 real 225x225 RNFLT OCT maps directly from
harvardairobotics/Harvard-GDP on Hugging Face using targeted HTTP Range requests,
pre-buffering the ~28.8MB contiguous block containing all RNFLT files to extract
all 1,000 records in seconds without downloading the 9.4GB 3D B-scan volume.
"""

import io
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path


class CachedRangeFile(io.RawIOBase):
    """File-like seekable stream reading from remote URL via HTTP Range requests with cache support."""

    def __init__(self, url: str):
        self.url = url
        self.pos = 0
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as res:
            self.length = int(res.headers["Content-Length"])
        self.cache_start = None
        self.cache_data = None

    def preload(self, start: int, end: int):
        size_mb = (end - start + 1) / (1024 * 1024)
        print(f"Pre-buffering range [{start} - {end}] ({size_mb:.2f} MB) in memory...")
        t0 = time.time()
        req = urllib.request.Request(
            self.url,
            headers={"Range": f"bytes={start}-{end}", "User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req) as res:
            self.cache_data = res.read()
        self.cache_start = start
        elapsed = time.time() - t0
        print(f"Pre-buffered {len(self.cache_data) / (1024 * 1024):.2f} MB in {elapsed:.2f}s ({len(self.cache_data) / (1024*1024) / max(elapsed, 0.001):.1f} MB/s).")

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.length + offset
        return self.pos

    def tell(self) -> int:
        return self.pos

    def readinto(self, b: bytearray) -> int:
        length = len(b)
        if self.pos >= self.length or length == 0:
            return 0
        end = min(self.pos + length - 1, self.length - 1)

        # Check if requested range is in cache
        if (
            self.cache_start is not None
            and self.cache_data is not None
            and self.cache_start <= self.pos
            and end < (self.cache_start + len(self.cache_data))
        ):
            rel_start = self.pos - self.cache_start
            rel_end = rel_start + (end - self.pos + 1)
            chunk = self.cache_data[rel_start:rel_end]
            b[: len(chunk)] = chunk
            self.pos += len(chunk)
            return len(chunk)

        # Fallback to direct range read (e.g. for Zip central directory lookup)
        req = urllib.request.Request(
            self.url,
            headers={"Range": f"bytes={self.pos}-{end}", "User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req) as res:
            data = res.read()
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)


def download_harvard_gdp_rnflt(
    dest_dir: str = "data/raw/harvard_gdp/rnflt_maps",
    max_count: int = 1000,
    report_interval: int = 100,
):
    """Extract real RNFLT maps from Hugging Face dataset.zip archive."""
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    url = "https://huggingface.co/datasets/harvardairobotics/Harvard-GDP/resolve/main/Dataset/dataset.zip"
    print("==================================================")
    print("HARVARD-GDP RNFLT MAP STREAM INGESTION")
    print(f"Source URL: {url}")
    print(f"Destination: {dest_path.resolve()}")
    print("Connecting to Hugging Face remote archive...")

    start_time = time.time()
    raw_stream = CachedRangeFile(url)
    stream = io.BufferedReader(raw_stream, buffer_size=1024 * 1024)
    zf = zipfile.ZipFile(stream)

    all_rnflt_entries = sorted(
        [z for z in zf.infolist() if z.filename.startswith("RNFLT/") and z.filename.endswith(".npz")],
        key=lambda x: x.filename,
    )
    total_available = len(all_rnflt_entries)
    print(f"Total RNFLT maps discovered in archive: {total_available}")

    target_entries = all_rnflt_entries[:max_count]
    print(f"Preparing to extract {len(target_entries)} records...")

    # Calculate span of target entries to pre-buffer
    sorted_by_offset = sorted(target_entries, key=lambda x: x.header_offset)
    min_offset = sorted_by_offset[0].header_offset
    max_offset = sorted_by_offset[-1].header_offset + sorted_by_offset[-1].compress_size + 8192

    raw_stream.preload(min_offset, max_offset)

    extracted = 0
    skipped = 0

    print("Extracting entries into local directory...")
    extract_start = time.time()
    for i, entry in enumerate(target_entries, 1):
        filename = os.path.basename(entry.filename)
        target_file = dest_path / filename

        with zf.open(entry) as src, open(target_file, "wb") as dst:
            dst.write(src.read())

        extracted += 1
        if i % report_interval == 0 or i == len(target_entries):
            elapsed = time.time() - extract_start
            print(f"  [{i}/{len(target_entries)}] Extracted: {extracted} | Time: {elapsed:.2f}s")

    total_time = time.time() - start_time
    total_files = len(list(dest_path.glob("*.npz")))
    print("--------------------------------------------------")
    print("DOWNLOAD COMPLETE")
    print(f"Extracted: {extracted}")
    print(f"Total Local Files in {dest_dir}: {total_files}")
    print(f"Total Ingestion Time: {total_time:.2f}s")
    print("==================================================")
    return total_files


if __name__ == "__main__":
    count = 1000
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    download_harvard_gdp_rnflt(max_count=count)
