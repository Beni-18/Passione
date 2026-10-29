"""Download only what Passione v2 needs from MicroLens-100k (Westlake University, github.com/westlake-repl/MicroLens).

Labels, titles and the interaction log (used only to estimate video age) are small files. The three embedding
matrices are pulled out of the 684 MB extracted_modality_features.zip with HTTP range requests, so only about
210 MB is transferred.
The dataset authors ask that modified copies are not redistributed: keep data/ out of git.
"""
import io, sys, urllib.request, zipfile
from pathlib import Path

BASE = "https://recsys.westlake.edu.cn/MicroLens-100k-Dataset"
OUT = Path(__file__).resolve().parent / "data"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SMALL = ["MicroLens-100k_likes_and_views.txt", "MicroLens-100k_title_en.csv", "MicroLens-100k_pairs.csv"]
MEMBERS = [
    "MicroLens-100k_video_features_VideoMAE.npy",
    "MicroLens-100k_image_features_CLIPRN50.npy",
    "MicroLens-100k_title_en_text_features_BgeM3.npy",
]


class RemoteFile(io.RawIOBase):
    """Seekable read-only view of a remote file, fetched in byte ranges."""

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        head = urllib.request.Request(url, method="HEAD", headers=HEADERS)
        self.size = int(urllib.request.urlopen(head, timeout=60).headers["Content-Length"])

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos

    def read(self, n=-1):
        n = self.size - self.pos if n < 0 else min(n, self.size - self.pos)
        if n <= 0:
            return b""
        req = urllib.request.Request(self.url, headers={**HEADERS, "Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        data = urllib.request.urlopen(req, timeout=300).read()
        self.pos += len(data)
        return data


def main() -> int:
    OUT.mkdir(exist_ok=True)
    for name in SMALL:
        if not (OUT / name).exists():
            req = urllib.request.Request(f"{BASE}/{name}", headers=HEADERS)
            (OUT / name).write_bytes(urllib.request.urlopen(req, timeout=300).read())
        print("ok", name)
    archive = zipfile.ZipFile(RemoteFile(f"{BASE}/extracted_modality_features.zip"))
    for name in MEMBERS:
        if not (OUT / name).exists():
            with archive.open(name) as src, open(OUT / name, "wb") as dst:
                while chunk := src.read(8 << 20):
                    dst.write(chunk)
        print("ok", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
