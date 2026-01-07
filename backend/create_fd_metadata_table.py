"""
Create FD Metadata table
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import engine
from models.fd_metadata import FDMetadata
from database.base import Base

def create_fd_metadata_table():
    """Create the fd_metadata table."""
    try:
        # Create the table
        Base.metadata.create_all(bind=engine, tables=[FDMetadata.__table__])
        print("✅ FD Metadata table created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    create_fd_metadata_table()

