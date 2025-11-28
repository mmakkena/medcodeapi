#!/usr/bin/env python3
"""
S3 Data Utilities for CDI Knowledge Base Migration

Provides utilities to download CDI knowledge base data from S3
for use in ECS batch tasks.

Usage:
    from scripts.s3_data_utils import get_data_path, download_from_s3

    # Automatically detects local vs S3 source
    source_path = get_data_path("knowledge_base/em_codes/em_codes.json")
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_S3_BUCKET = "nuvii-data-793523315434"
DEFAULT_S3_PREFIX = "cdi-knowledge-base"
DEFAULT_LOCAL_ROOT = Path("/Users/murali.local/CDIAgent")

# Environment variables for configuration
S3_BUCKET = os.environ.get("CDI_S3_BUCKET", DEFAULT_S3_BUCKET)
S3_PREFIX = os.environ.get("CDI_S3_PREFIX", DEFAULT_S3_PREFIX)
LOCAL_ROOT = Path(os.environ.get("CDI_LOCAL_ROOT", str(DEFAULT_LOCAL_ROOT)))
USE_S3 = os.environ.get("CDI_USE_S3", "false").lower() == "true"

# Temp directory for S3 downloads
TEMP_DATA_DIR = Path(tempfile.gettempdir()) / "cdi_knowledge_base"


def is_running_in_ecs() -> bool:
    """Check if running in ECS environment."""
    return os.environ.get("ECS_CONTAINER_METADATA_URI") is not None


def should_use_s3() -> bool:
    """Determine if S3 should be used as data source."""
    # Explicitly set via environment
    if USE_S3:
        return True

    # Auto-detect ECS environment
    if is_running_in_ecs():
        return True

    # Check if local path exists
    if not LOCAL_ROOT.exists():
        logger.info(f"Local root {LOCAL_ROOT} not found, will use S3")
        return True

    return False


def download_from_s3(s3_path: str, local_path: Path) -> Path:
    """
    Download file or directory from S3.

    Args:
        s3_path: S3 key (relative to prefix)
        local_path: Local destination path

    Returns:
        Path to downloaded file/directory
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise ImportError("boto3 required for S3 operations. Install with: pip install boto3")

    s3 = boto3.client('s3')
    full_s3_key = f"{S3_PREFIX}/{s3_path}"

    logger.info(f"Downloading from s3://{S3_BUCKET}/{full_s3_key}")

    # Ensure parent directory exists
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Check if it's a file or directory by listing objects
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=full_s3_key,
            MaxKeys=1
        )

        if 'Contents' not in response:
            raise FileNotFoundError(f"S3 object not found: {full_s3_key}")

        # If the key ends with / or there are multiple objects, it's a directory
        objects = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=full_s3_key
        )

        if objects.get('KeyCount', 0) > 1 or full_s3_key.endswith('/'):
            # Download directory
            local_path.mkdir(parents=True, exist_ok=True)

            for obj in objects.get('Contents', []):
                key = obj['Key']
                relative_path = key[len(full_s3_key):].lstrip('/')

                if not relative_path:
                    continue

                file_local_path = local_path / relative_path
                file_local_path.parent.mkdir(parents=True, exist_ok=True)

                logger.debug(f"  Downloading {key} -> {file_local_path}")
                s3.download_file(S3_BUCKET, key, str(file_local_path))

            logger.info(f"Downloaded directory to {local_path}")
        else:
            # Download single file
            s3.download_file(S3_BUCKET, full_s3_key, str(local_path))
            logger.info(f"Downloaded file to {local_path}")

        return local_path

    except ClientError as e:
        logger.error(f"S3 error: {e}")
        raise


def get_data_path(
    relative_path: str,
    force_s3: bool = False,
    force_local: bool = False
) -> Path:
    """
    Get path to CDI knowledge base data, downloading from S3 if needed.

    Args:
        relative_path: Path relative to CDIAgent root (e.g., "knowledge_base/em_codes/em_codes.json")
        force_s3: Force download from S3 even if local exists
        force_local: Force use of local path even if not found

    Returns:
        Path to the data (local or downloaded)

    Raises:
        FileNotFoundError: If data not found locally and S3 download fails
    """
    # Check local path first
    local_path = LOCAL_ROOT / relative_path

    if force_local:
        return local_path

    if not force_s3 and local_path.exists():
        logger.debug(f"Using local path: {local_path}")
        return local_path

    # Download from S3
    if force_s3 or should_use_s3():
        temp_path = TEMP_DATA_DIR / relative_path

        # Check if already downloaded
        if temp_path.exists() and not force_s3:
            logger.debug(f"Using cached S3 download: {temp_path}")
            return temp_path

        return download_from_s3(relative_path, temp_path)

    # Fall back to local path (may not exist)
    return local_path


def get_em_codes_path() -> Path:
    """Get path to E/M codes JSON file."""
    return get_data_path("knowledge_base/em_codes/em_codes.json")


def get_investigations_path() -> Path:
    """Get path to investigations directory."""
    return get_data_path("knowledge_base/investigations")


def get_cdi_documents_path() -> Path:
    """Get path to CDI documents directory."""
    return get_data_path("cdi_documents")


def setup_s3_data_paths() -> dict:
    """
    Setup all data paths, downloading from S3 if needed.

    Returns:
        Dict with paths to all data sources
    """
    logger.info("Setting up CDI knowledge base data paths...")

    use_s3 = should_use_s3()
    logger.info(f"Data source: {'S3' if use_s3 else 'Local'}")

    paths = {
        'em_codes': get_em_codes_path(),
        'investigations': get_investigations_path(),
        'cdi_documents': get_cdi_documents_path(),
    }

    # Verify paths exist
    for name, path in paths.items():
        if path.exists():
            logger.info(f"  {name}: {path} [OK]")
        else:
            logger.warning(f"  {name}: {path} [NOT FOUND]")

    return paths


def cleanup_temp_data():
    """Remove temporary S3 downloads."""
    import shutil

    if TEMP_DATA_DIR.exists():
        logger.info(f"Cleaning up temp data: {TEMP_DATA_DIR}")
        shutil.rmtree(TEMP_DATA_DIR)


if __name__ == "__main__":
    # Test the utilities
    logging.basicConfig(level=logging.INFO)

    print("CDI Knowledge Base Data Utilities")
    print("=" * 50)
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"S3 Prefix: {S3_PREFIX}")
    print(f"Local Root: {LOCAL_ROOT}")
    print(f"Use S3: {should_use_s3()}")
    print(f"Running in ECS: {is_running_in_ecs()}")
    print()

    paths = setup_s3_data_paths()
    print()
    print("Data paths:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
