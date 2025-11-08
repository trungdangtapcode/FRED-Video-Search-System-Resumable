import json
import os
from datetime import datetime
from threading import Lock
from typing import Dict, Literal


class DownloadLogger:
    """Thread-safe logger for download and unzip operations with resume support"""

    def __init__(self, log_file: str = "download_log.json"):
        self.log_file = log_file
        self.lock = Lock()
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load existing state from log file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"downloads": {}, "unzips": {}, "metadata": {}}
        return {"downloads": {}, "unzips": {}, "metadata": {}}

    def _save_state(self):
        """Save current state to log file"""
        with self.lock:
            try:
                with open(self.log_file, "w") as f:
                    json.dump(self.state, f, indent=2)
            except IOError as e:
                print(f"Warning: Could not save log: {e}")

    def log_download(
        self,
        url: str,
        status: Literal["pending", "downloading", "completed", "failed", "skipped"],
        size: int = 0,
        error: str = None,
    ):
        """Log download status"""
        filename = os.path.basename(url.split("?")[0])
        with self.lock:
            self.state["downloads"][filename] = {
                "url": url,
                "status": status,
                "size": size,
                "timestamp": datetime.now().isoformat(),
                "error": error,
            }
        self._save_state()

    def log_unzip(
        self,
        zip_file: str,
        status: Literal["pending", "extracting", "completed", "failed", "skipped"],
        files_count: int = 0,
        error: str = None,
    ):
        """Log unzip status"""
        filename = os.path.basename(zip_file)
        with self.lock:
            self.state["unzips"][filename] = {
                "zip_file": zip_file,
                "status": status,
                "files_count": files_count,
                "timestamp": datetime.now().isoformat(),
                "error": error,
            }
        self._save_state()

    def is_download_complete(self, url: str) -> bool:
        """Check if download is already completed"""
        filename = os.path.basename(url.split("?")[0])
        return (
            filename in self.state["downloads"]
            and self.state["downloads"][filename]["status"] == "completed"
        )

    def is_unzip_complete(self, zip_file: str) -> bool:
        """Check if unzip is already completed"""
        filename = os.path.basename(zip_file)
        return (
            filename in self.state["unzips"]
            and self.state["unzips"][filename]["status"] == "completed"
        )

    def get_summary(self) -> Dict:
        """Get summary of all operations"""
        downloads = self.state["downloads"]
        unzips = self.state["unzips"]

        return {
            "downloads": {
                "total": len(downloads),
                "completed": sum(
                    1 for d in downloads.values() if d["status"] == "completed"
                ),
                "failed": sum(1 for d in downloads.values() if d["status"] == "failed"),
                "pending": sum(
                    1
                    for d in downloads.values()
                    if d["status"] in ["pending", "downloading"]
                ),
            },
            "unzips": {
                "total": len(unzips),
                "completed": sum(
                    1 for u in unzips.values() if u["status"] == "completed"
                ),
                "failed": sum(1 for u in unzips.values() if u["status"] == "failed"),
                "pending": sum(
                    1
                    for u in unzips.values()
                    if u["status"] in ["pending", "extracting"]
                ),
            },
        }

    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()
        print("\n" + "=" * 50)
        print("DOWNLOAD & UNZIP SUMMARY")
        print("=" * 50)
        print(f"\nDownloads:")
        print(f"  Total:     {summary['downloads']['total']}")
        print(f"  Completed: {summary['downloads']['completed']} ✅")
        print(f"  Failed:    {summary['downloads']['failed']} ❌")
        print(f"  Pending:   {summary['downloads']['pending']} ⏳")
        print(f"\nUnzips:")
        print(f"  Total:     {summary['unzips']['total']}")
        print(f"  Completed: {summary['unzips']['completed']} ✅")
        print(f"  Failed:    {summary['unzips']['failed']} ❌")
        print(f"  Pending:   {summary['unzips']['pending']} ⏳")
        print("=" * 50 + "\n")

    def get_failed_items(self) -> Dict:
        """Get all failed downloads and unzips with error messages"""
        failed = {"downloads": [], "unzips": []}

        for filename, info in self.state["downloads"].items():
            if info["status"] == "failed":
                failed["downloads"].append(
                    {
                        "filename": filename,
                        "url": info["url"],
                        "error": info.get("error", "Unknown"),
                    }
                )

        for filename, info in self.state["unzips"].items():
            if info["status"] == "failed":
                failed["unzips"].append(
                    {
                        "filename": filename,
                        "path": info["zip_file"],
                        "error": info.get("error", "Unknown"),
                    }
                )

        return failed

    def print_failed_items(self):
        """Print all failed items for debugging"""
        failed = self.get_failed_items()

        if not failed["downloads"] and not failed["unzips"]:
            print("\n✅ No failed items!")
            return

        print("\n" + "=" * 50)
        print("FAILED ITEMS (for debugging)")
        print("=" * 50)

        if failed["downloads"]:
            print("\nFailed Downloads:")
            for item in failed["downloads"]:
                print(f"  ❌ {item['filename']}")
                print(f"     URL: {item['url']}")
                print(f"     Error: {item['error']}\n")

        if failed["unzips"]:
            print("\nFailed Unzips:")
            for item in failed["unzips"]:
                print(f"  ❌ {item['filename']}")
                print(f"     Path: {item['path']}")
                print(f"     Error: {item['error']}\n")

        print("=" * 50 + "\n")
