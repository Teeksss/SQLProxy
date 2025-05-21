"""
Backup Cron Job for SQL Proxy

This module provides scheduled backup capabilities via cron jobs.

Last updated: 2025-05-20 10:59:28
Updated by: Teeksss
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.backup.backup_manager import backup_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging for cron job"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = logging.INFO
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.BACKUP_LOG_FILE)
        ]
    )

def run_backup():
    """Run backup as a cron job"""
    setup_logging()
    
    logger.info("Starting scheduled backup")
    start_time = time.time()
    
    try:
        # Generate backup name with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"scheduled_backup_{timestamp}"
        
        # Create backup
        result = backup_manager.create_backup(backup_name)
        
        if "error" in result:
            logger.error(f"Backup failed: {result['error']}")
            sys.exit(1)
        
        # Log success
        duration = time.time() - start_time
        logger.info(f"Scheduled backup completed successfully in {duration:.2f}s: {result['backup_file']}")
        
    except Exception as e:
        logger.exception(f"Error running scheduled backup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()

# Son güncelleme: 2025-05-20 10:59:28
# Güncelleyen: Teeksss