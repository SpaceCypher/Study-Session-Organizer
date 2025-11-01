import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MySQL database connections and operations"""
    
    def __init__(self, config):
        """Initialize with database configuration"""
        self.config = config
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
                logger.info("Successfully connected to MySQL database")
            return self.connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise
    
    def get_cursor(self, dictionary=True):
        """Get cursor for database operations"""
        if self.connection is None or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=dictionary)
    
    def execute_query(self, query, params=None):
        """Execute SELECT query and return results"""
        try:
            cursor = self.get_cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_update(self, query, params=None):
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            cursor = self.get_cursor(dictionary=False)
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            last_id = cursor.lastrowid
            cursor.close()
            
            # Commit if autocommit is disabled
            if not self.config.get('autocommit', True):
                self.connection.commit()
                
            return {'affected_rows': affected_rows, 'last_id': last_id}
        except Error as e:
            logger.error(f"Error executing update: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            if not self.config.get('autocommit', True):
                self.connection.rollback()
            raise
    
    def call_procedure(self, proc_name, args=None):
        """
        Call stored procedure with arguments
        Returns tuple: (results, out_params)
        """
        try:
            cursor = self.get_cursor(dictionary=True)
            
            # Call procedure
            result_args = cursor.callproc(proc_name, args or [])
            
            # Fetch all result sets
            results = []
            for result in cursor.stored_results():
                results.append(result.fetchall())
            
            cursor.close()
            
            return results, result_args
        except Error as e:
            logger.error(f"Error calling procedure {proc_name}: {e}")
            logger.error(f"Args: {args}")
            raise
    
    def execute_function(self, query):
        """Execute query that calls a MySQL function"""
        return self.execute_query(query)
    
    def close(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info("MySQL connection closed")
        except Error as e:
            logger.error(f"Error closing connection: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
