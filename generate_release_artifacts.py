import os
import sys
import asyncio
import logging
import time
from datetime import datetime

# Add current directory to path to allow imports from src
sys.path.append(os.getcwd())

from src.services.backup_service import BackupService
from src.services.performance_service import PerformanceService
from src.core.database_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def generate_artifacts():
    logger.info("Starting artifact generation for v5.2.1...")
    
    # Ensure directories exist
    os.makedirs("release_artifacts", exist_ok=True)

    # Initialize DB Manager
    db_path = "accounting.db"
    if not os.path.exists(db_path):
        logger.warning("accounting.db not found, creating empty file for testing")
        with open(db_path, "w") as f:
            f.write("") 
            
    db_manager = DatabaseManager(db_path=db_path)
    
    # 1. Generate Sample Backup
    logger.info("Generating sample backup...")
    backup_service = BackupService(db_manager)

    try:
        # Create a backup
        # Note: create_backup is synchronous in this version based on file read, 
        # but if it was async we would await it. The file showed def create_backup, not async def.
        # Wait, let's check if it is async. The file snippet showed "def create_backup".
        # So we should NOT await it.
        
        result = backup_service.create_backup(
            description="Release v5.2.1 Sample Backup",
            compress=True
        )
        
        if result.get('success'):
            backup_path = result.get('path')
            logger.info(f"Backup created at: {backup_path}")
            
            # Copy to release_artifacts for visibility
            if backup_path and os.path.exists(backup_path):
                dest_name = os.path.basename(backup_path)
                dest_path = os.path.join("release_artifacts", dest_name)
                with open(backup_path, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())
                logger.info(f"Copied backup to: {dest_path}")
        else:
            logger.error(f"Backup failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Backup generation failed: {e}")

    # 2. Generate Sample Metrics Export
    logger.info("Generating sample metrics export...")
    perf_service = PerformanceService(db_manager)
    
    # Record some dummy metrics by collecting current state and appending to history
    # We'll do it a few times to have some history
    for _ in range(5):
        metrics = perf_service.collect_current_metrics()
        # Simulate some activity
        metrics.query_count = 10 + _ * 5
        metrics.avg_query_time_ms = 5.0 + _
        perf_service.metrics_history.append(metrics)
        time.sleep(0.1)
    
    try:
        # Export metrics
        json_path = os.path.join("release_artifacts", "sample_metrics_v5.2.1.json")
        res_json = perf_service.export_metrics_to_json(json_path)
        logger.info(f"Metrics exported to JSON: {res_json}")
        
        csv_path = os.path.join("release_artifacts", "sample_metrics_v5.2.1.csv")
        res_csv = perf_service.export_metrics_to_csv(csv_path)
        logger.info(f"Metrics exported to CSV: {res_csv}")
        
    except Exception as e:
        logger.error(f"Metrics export failed: {e}")

    logger.info("Artifact generation complete.")

if __name__ == "__main__":
    asyncio.run(generate_artifacts())
