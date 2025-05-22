import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
from src.configDict import Setting
from src.db_config import Base

import logging


# Set logging level to ERROR to minimize output
logging.basicConfig(level=logging.ERROR)

# Disable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)

class DatabaseManager:
    def __init__(self):
        self.setting = Setting()
        self.database_name = self.setting.database_name
        self._setup_connection_params()
        # self.base = declarative_base()
        logging.info(f"DatabaseManager: Initialized with database_name: {self.database_name}")

    def get_db(self):
        """
        Returns a database session.  Use this as a context manager.
        """
        if not self.session_local:
            raise Exception("Database not initialized. Call initialize() first.")
        db = self.session_local()
        try:
            yield db
        finally:
            db.close()

    def _setup_connection_params(self):
        """Set up connection parameters with proper encoding"""
        try:
            # URL encode all parameters to handle special characters
            encoded_password = quote_plus(str(self.setting.database_password))
            encoded_username = quote_plus(str(self.setting.database_username))
            encoded_hostname = quote_plus(str(self.setting.database_hostname))
            encoded_dbname = quote_plus(str(self.database_name))
            
            self.connection_params = {
                'host': encoded_hostname,
                'port': str(self.setting.database_port),
                'user': encoded_username,
                'password': encoded_password,
                'client_encoding': 'UTF8',
                'options': '-c client_encoding=UTF8'
            }
            
            # Construct SQLAlchemy URL with encoded parameters
            self.sqlalchemy_database_url = (
                f"postgresql://{encoded_username}:{encoded_password}"
                f"@{encoded_hostname}:{self.setting.database_port}/{encoded_dbname}"
            )
            logging.info("Connection parameters set up successfully")
        except Exception as e:
            logging.error(f"Error setting up connection parameters: {str(e)}")
            raise

    def create_database_if_not_exists(self):
        try:
            # Connect to default postgres database first
            temp_params = self.connection_params.copy()
            temp_params['dbname'] = 'postgres'
            
            conn = psycopg2.connect(**temp_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.database_name,))
                exists = cur.fetchone()
                
                if not exists:
                    # Create database with UTF-8 encoding
                    cur.execute(
                        f'CREATE DATABASE "{self.database_name}" '
                        f'TEMPLATE template0 '
                        f'ENCODING \'UTF8\' '
                        f'LC_COLLATE \'en_US.UTF-8\' '
                        f'LC_CTYPE \'en_US.UTF-8\''
                    )
                    logging.info(f"Database '{self.database_name}' created successfully")
                else:
                    logging.info(f"Database '{self.database_name}' already exists")
            
            conn.close()
        except Exception as e:
            logging.error(f"Error in create_database_if_not_exists: {str(e)}")
            raise

    def initialize(self):
        try:
            # Create database if it doesn't exist
            self.create_database_if_not_exists()
            
            # Create SQLAlchemy engine with proper encoding
            self.engine = create_engine(
                self.sqlalchemy_database_url,
                echo=False,
                pool_pre_ping=True,
                connect_args={'client_encoding': 'utf8'}
            )
            
            # Create session factory
            self.session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
    
            logging.info("Database initialized successfully")
            
        except Exception as e:
            logging.error(f"Error in initialize: {str(e)}")
            raise

# Singleton instance
db_manager = DatabaseManager()
db_manager.initialize()

# Export commonly used objects
engine = db_manager.engine
SessionLocal = db_manager.session_local
get_db = db_manager.get_db
