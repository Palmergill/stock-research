from sqlalchemy import inspect, text
from app.database import engine, Base
import logging

logger = logging.getLogger(__name__)

def migrate_database():
    """Auto-migrate database schema without losing data"""
    try:
        inspector = inspect(engine)
        
        # Check if stock_summaries table exists
        if 'stock_summaries' in inspector.get_table_names():
            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns('stock_summaries')]
            
            # Define expected columns from model
            from app.database import StockSummary
            expected_columns = [col.name for col in StockSummary.__table__.columns]
            
            # Add missing columns
            for col_name in expected_columns:
                if col_name not in existing_columns and col_name != 'id':
                    logger.info(f"Adding column {col_name} to stock_summaries")
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE stock_summaries ADD COLUMN {col_name} FLOAT"))
                            conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not add column {col_name}: {e}")
        
        # Same for earnings table
        if 'earnings' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('earnings')]
            
            from app.database import EarningsRecord
            expected_columns = [col.name for col in EarningsRecord.__table__.columns]
            
            for col_name in expected_columns:
                if col_name not in existing_columns and col_name != 'id':
                    logger.info(f"Adding column {col_name} to earnings")
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE earnings ADD COLUMN {col_name} FLOAT"))
                            conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not add column {col_name}: {e}")
        
        logger.info("Database migration complete")
        
    except Exception as e:
        logger.error(f"Migration error: {e}")

def init_db_with_migration():
    """Initialize DB with auto-migration"""
    try:
        # First try to migrate existing tables
        migrate_database()
    except:
        pass
    
    # Then create any missing tables
    Base.metadata.create_all(bind=engine)
