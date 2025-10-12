"""
GraphQL client for querying ISO files from API
"""

import asyncio
import json
import os
from typing import List, Dict, Optional, Any
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import aiohttp
import logging

from config import Config


class GraphQLClient:
    """GraphQL client for querying ISO files."""

    def __init__(self, config: Config):
        """Initialize GraphQL client.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize transport
        headers = {}
        if self.config.api_key:
            headers['Authorization'] = f'Token {self.config.api_key}'

        self.transport = AIOHTTPTransport(
            url=self.config.graphql_endpoint,
            headers=headers,
            timeout=self.config.api_timeout  # Pass timeout directly as seconds
        )

        # Initialize client
        self.client = Client(transport=self.transport, fetch_schema_from_transport=False)

    async def query_new_isos(self, last_check_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query for new ISO files since last check.

        Args:
            last_check_time: ISO 8601 timestamp of last check

        Returns:
            List of new ISO file information
        """
        try:
            # GraphQL query for new ISOs
            query_string = '''
            query isosByBurner($burner: UUID!) {
                downloadIsosByBurner(burner: $burner) {
                    id
                    study {
                    patient{
                        fullName
                        identifier
                        birthDate
                    }
                    dicomDateTime
                    dicomDescription
                    }
                    fileUrl
                }
            }
            '''

            query = gql(query_string)

            variables = {
                'burner': self.config.robot_uuid    
            }
            # if last_check_time:
            #     variables['lastCheckTime'] = last_check_time

            # Execute query with retry logic
            max_retries = self.config.config_data['api']['retry_attempts']
            for attempt in range(max_retries):
                try:
                    result = await self.client.execute_async(query, variable_values=variables)
                    return result.get('downloadIsosByBurner', [])
                except Exception as e:
                    self.logger.warning(f"Query attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        except Exception as e:
            self.logger.error(f"Error querying new ISOs: {e}")
            return []

    async def download_iso_file(self, iso_info: Dict[str, Any], download_path: str) -> bool:
        """Download ISO file from URL.

        Args:
            iso_info: ISO file information from GraphQL query
            download_path: Local path to save the file

        Returns:
            True if download successful, False otherwise
        """
        download_url = iso_info.get('fileUrl')
        if not download_url:
            self.logger.error(f"No download URL for ISO: {iso_info.get('id')}")
            return False

        try:
            # Ensure download directory exists
            download_dir = os.path.dirname(download_path)
            os.makedirs(download_dir, exist_ok=True)

            # Download with progress tracking
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status != 200:
                        self.logger.error(f"Download failed with status {response.status}")
                        return False

                    # Get file size for progress tracking
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        total_size = int(content_length)
                    else:
                        total_size = None

                    # Download in chunks
                    with open(download_path, 'wb') as f:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size:
                                progress = (downloaded / total_size) * 100
                                self.logger.debug(f"Download progress: {progress:.1f}%")

            # Verify file size if provided
            if 'fileSize' in iso_info:
                actual_size = os.path.getsize(download_path)
                expected_size = iso_info['fileSize']
                if actual_size != expected_size:
                    self.logger.error(f"File size mismatch: expected {expected_size}, got {actual_size}")
                    os.remove(download_path)
                    return False

            # Verify checksum if provided
            if 'checksum' in iso_info:
                if not self._verify_checksum(download_path, iso_info['checksum']):
                    self.logger.error(f"Checksum verification failed for {download_path}")
                    os.remove(download_path)
                    return False

            self.logger.info(f"Successfully downloaded ISO: {download_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error downloading ISO: {e}")
            # Clean up partial download
            if os.path.exists(download_path):
                os.remove(download_path)
            return False

    def _verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify file checksum.

        Args:
            file_path: Path to file to verify
            expected_checksum: Expected checksum

        Returns:
            True if checksum matches, False otherwise
        """
        import hashlib

        try:
            # Parse checksum format (assume MD5 for now, can be extended)
            if ':' in expected_checksum:
                algorithm, checksum = expected_checksum.split(':', 1)
            else:
                algorithm, checksum = 'md5', expected_checksum

            algorithm = algorithm.lower()
            checksum = checksum.lower()

            # Calculate actual checksum
            hash_func = getattr(hashlib, algorithm)()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)

            actual_checksum = hash_func.hexdigest()
            return actual_checksum == checksum

        except Exception as e:
            self.logger.error(f"Error verifying checksum: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test connection to GraphQL API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple test query
            test_query = gql('query { __typename }')
            await self.client.execute_async(test_query)
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def get_iso_info(self, iso_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific ISO.

        Args:
            iso_id: ISO identifier

        Returns:
            ISO information or None if not found
        """
        # This would typically be implemented with a specific GraphQL query
        # For now, return None as this depends on the actual API schema
        self.logger.warning(f"get_iso_info not implemented for ISO: {iso_id}")
        return None


# Synchronous wrapper for easier integration
class SyncGraphQLClient:
    """Synchronous wrapper for GraphQL client."""

    def __init__(self, config: Config):
        self.config = config
        self.client = GraphQLClient(config)

    def query_new_isos(self, last_check_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """Synchronous version of query_new_isos."""
        return asyncio.run(self.client.query_new_isos(last_check_time))

    def download_iso_file(self, iso_info: Dict[str, Any], download_path: str) -> bool:
        """Synchronous version of download_iso_file."""
        return asyncio.run(self.client.download_iso_file(iso_info, download_path))

    def test_connection(self) -> bool:
        """Synchronous version of test_connection."""
        return asyncio.run(self.client.test_connection())
