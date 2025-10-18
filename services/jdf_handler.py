from pathlib import Path


class JDFHandler:
    """
    Handler for JDF files (EPSON PP-100 workflow).

    Usage:
        handler = JDFHandler("/path/to/jobfile.jdf")
        handler.create_if_not_exists()
        exists = handler.exists()
        state = handler.get_status()
    """

    class Status:
        WAITING = "WAITING"  # JDF file exists, job waiting to be picked up
        PROCESSING = "PROCESSING"  # INP file exists, disk burner is processing
        ERROR = "ERROR"  # ERR file exists, job failed
        SUCCESS = "SUCCESS"  # DON file exists, job done
        NOT_FOUND = "NOT_FOUND"  # No corresponding file

    def __init__(self, jdf_file_path):
        """
        Args:
            jdf_file_path (str or Path): Path to the intended JDF file (with .jdf extension)
        """
        if not jdf_file_path:
            raise ValueError("JDF file path must be provided")
        self.base_path = Path(jdf_file_path)
        self.parent = self.base_path.parent
        self.stem = self.base_path.stem  # Filename without suffix

    def exists(self):
        """
        Check if any known file matching this job (JDF/INP/DON/ERR, with possible suffix) exists.

        Returns:
            bool: True if any matching file exists
        """
        for ext in ["JDF", "INP", "ERR", "DON"]:
            matches = list(self.parent.glob(f"{self.stem}*.{ext}"))
            if matches:
                return True
        return False

    def create_if_not_exists(self):
        """
        Create the JDF file if it does not already exist.
        """
        jdf_file = self.parent / f"{self.stem}.JDF"
        if not jdf_file.exists():
            jdf_file.touch()

    def get_status(self):
        """
        Identify the current state of the JDF job based on file extension.

        Returns:
            str: One of JDFHandler.Status
        """
        # Priority order: ERR > DON > INP > JDF
        file_ext_map = [
            ("ERR", JDFHandler.Status.ERROR),
            ("DON", JDFHandler.Status.SUCCESS),
            ("INP", JDFHandler.Status.PROCESSING),
            ("JDF", JDFHandler.Status.WAITING),
        ]
        for ext, status in file_ext_map:
            matches = sorted(self.parent.glob(f"{self.stem}*.{ext}"))
            if matches:
                return status
        return JDFHandler.Status.NOT_FOUND

    def get_matching_files(self):
        """
        Return a dict of lists: {ext: [Path, ...]} for each known extension this job may have.

        Returns:
            dict: {'JDF': [...], 'INP': [...], 'ERR': [...], 'DON': [...]}
        """
        result = {}
        for ext in ["JDF", "INP", "ERR", "DON"]:
            result[ext] = list(self.parent.glob(f"{self.stem}*.{ext}"))
        return result

    def get_jdf_path(self):
        """
        Return the path to the JDF file.
        """
        return self.base_path

    @property
    def status(self):
        """
        Return the status of the JDF job.
        """
        return self.get_status()

    def __repr__(self):
        return f"<JDFHandler base='{self.base_path}'>"
