"""
ISO Download Manager with progress tracking
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from config import Config
from graphql_client import SyncGraphQLClient


class DownloadProgress:
    """Progress information for a download."""

    def __init__(self, iso_id: str, filename: str, total_size: int = 0):
        self.iso_id = iso_id
        self.filename = filename
        self.total_size = total_size
        self.downloaded_size = 0
        self.start_time = time.time()
        self.status = "pending"  # pending, downloading, completed, failed, cancelled
        self.error_message: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate download progress percentage."""
        if self.total_size == 0:
            return 0.0
        return (self.downloaded_size / self.total_size) * 100.0

    @property
    def speed_bps(self) -> float:
        """Calculate download speed in bytes per second."""
        elapsed = time.time() - self.start_time
        if elapsed == 0 or self.downloaded_size == 0:
            return 0.0
        return self.downloaded_size / elapsed

    @property
    def eta_seconds(self) -> Optional[float]:
        """Estimate time remaining in seconds."""
        if self.total_size == 0 or self.speed_bps == 0:
            return None
        remaining = self.total_size - self.downloaded_size
        return remaining / self.speed_bps


class ISODownloadManager:
    """Manager for downloading ISO files with progress tracking."""

    def __init__(self, config: Config):
        """Initialize download manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize GraphQL client
        self.graphql_client = SyncGraphQLClient(config)

        # Download tracking
        self.active_downloads: Dict[str, DownloadProgress] = {}
        self.completed_downloads: List[DownloadProgress] = []

        # Progress callbacks
        self.progress_callbacks: List[Callable[[str, DownloadProgress], None]] = []

        # Ensure download folder exists
        self.config.ensure_folders_exist()

    def add_progress_callback(self, callback: Callable[[str, DownloadProgress], None]):
        """Add a callback for download progress updates.

        Args:
            callback: Function that receives (iso_id, progress) updates
        """
        self.progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[str, DownloadProgress], None]):
        """Remove a progress callback.

        Args:
            callback: The callback function to remove
        """
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)

    def _notify_progress(self, iso_id: str, progress: DownloadProgress):
        """Notify all callbacks of progress update."""
        for callback in self.progress_callbacks:
            try:
                callback(iso_id, progress)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")

    def download_iso(self, iso_info: Dict[str, Any]) -> str:
        """Download an ISO file.

        Args:
            iso_info: ISO information from GraphQL query

        Returns:
            Path to downloaded file or empty string if failed
        """
        iso_id = iso_info.get("id")
        if not iso_id:
            self.logger.error("ISO info missing ID")
            return ""

        filename = iso_info.get("filename", f"iso_{iso_id}.iso")
        download_path = self.config.downloads_folder / filename

        # Check if file already exists
        if download_path.exists():
            self.logger.info(f"ISO file already exists: {download_path}")
            return str(download_path)

        # Create progress tracker
        progress = DownloadProgress(iso_id, filename)
        self.active_downloads[iso_id] = progress
        self._notify_progress(iso_id, progress)

        try:
            # Start download
            progress.status = "downloading"
            self._notify_progress(iso_id, progress)

            success = self.graphql_client.download_iso_file(iso_info, str(download_path))

            if success:
                progress.status = "completed"
                progress.downloaded_size = download_path.stat().st_size
                self.completed_downloads.append(progress)
                self.logger.info(f"Successfully downloaded ISO: {download_path}")
                self._notify_progress(iso_id, progress)
                return str(download_path)
            else:
                progress.status = "failed"
                progress.error_message = "Download failed"
                self._notify_progress(iso_id, progress)
                return ""

        except Exception as e:
            progress.status = "failed"
            progress.error_message = str(e)
            self.logger.error(f"Error downloading ISO {iso_id}: {e}")
            self._notify_progress(iso_id, progress)
            return ""
        finally:
            # Clean up active downloads
            if iso_id in self.active_downloads:
                del self.active_downloads[iso_id]

    def download_isos_batch(self, iso_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """Download multiple ISO files.

        Args:
            iso_list: List of ISO information dictionaries

        Returns:
            Dictionary mapping ISO IDs to download paths
        """
        results = {}
        for iso_info in iso_list:
            iso_id = iso_info.get("id")
            if iso_id:
                download_path = self.download_iso(iso_info)
                results[iso_id] = download_path

        return results

    def get_active_downloads(self) -> Dict[str, DownloadProgress]:
        """Get current active downloads.

        Returns:
            Dictionary of active downloads by ISO ID
        """
        return self.active_downloads.copy()

    def get_completed_downloads(self) -> List[DownloadProgress]:
        """Get recently completed downloads.

        Returns:
            List of completed download progress objects
        """
        return self.completed_downloads.copy()

    def cancel_download(self, iso_id: str) -> bool:
        """Cancel an active download.

        Args:
            iso_id: ID of the ISO to cancel

        Returns:
            True if cancelled successfully, False if not found
        """
        if iso_id in self.active_downloads:
            progress = self.active_downloads[iso_id]
            progress.status = "cancelled"
            progress.error_message = "Cancelled by user"

            # Remove from active downloads
            del self.active_downloads[iso_id]

            self._notify_progress(iso_id, progress)
            self.logger.info(f"Cancelled download for ISO: {iso_id}")
            return True

        return False

    def cleanup_old_downloads(self, max_age_hours: int = 24):
        """Clean up old completed downloads from memory.

        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)

        # Remove old completed downloads
        self.completed_downloads = [
            progress for progress in self.completed_downloads if progress.start_time > cutoff_time
        ]

        self.logger.debug(f"Cleaned up old downloads, {len(self.completed_downloads)} remaining")

    def get_download_stats(self) -> Dict[str, Any]:
        """Get download statistics.

        Returns:
            Dictionary with download statistics
        """
        total_completed = len(self.completed_downloads)
        total_active = len(self.active_downloads)

        # Calculate success rate
        if total_completed > 0:
            successful = len([p for p in self.completed_downloads if p.status == "completed"])
            success_rate = (successful / total_completed) * 100
        else:
            success_rate = 0.0

        return {
            "active_downloads": total_active,
            "completed_downloads": total_completed,
            "success_rate": success_rate,
            "total_size_downloaded": sum(p.downloaded_size for p in self.completed_downloads),
        }

    def test_api_connection(self) -> bool:
        """Test connection to the API.

        Returns:
            True if connection successful, False otherwise
        """
        return self.graphql_client.test_connection()
