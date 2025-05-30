"""
Database Optimization Utilities for Think-Tank.

This module provides tools and utilities for optimizing database operations:
- Query optimization and profiling
- Connection pooling and management
- Caching strategies for database queries
- Batch processing for improved performance
- Index management and recommendations
- Query logging and analysis
"""

import time
import logging
import functools
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Set, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager

# SQLAlchemy imports
from sqlalchemy import create_engine, text, event, inspect, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Select, Insert, Update, Delete
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.exc import SQLAlchemyError

# Local imports
from config import settings
from caching import cached, get_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_optimizations")

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Constants
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 3600  # 1 hour
DEFAULT_CACHE_TTL = 300  # 5 minutes
DEFAULT_BATCH_SIZE = 100
DEFAULT_SLOW_QUERY_THRESHOLD_MS = 100


@dataclass
class QueryMetrics:
    """Metrics for database queries."""
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0
    row_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "parameters": self.parameters,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "timestamp": self.timestamp.isoformat(),
            "cache_hit": self.cache_hit,
        }
    
    def is_slow(self, threshold_ms: float = DEFAULT_SLOW_QUERY_THRESHOLD_MS) -> bool:
        """Check if this is a slow query."""
        return self.execution_time_ms > threshold_ms


class QueryProfiler:
    """
    Utility for profiling and analyzing database queries.
    
    This class provides tools for:
    - Measuring query execution time
    - Logging slow queries
    - Collecting query statistics
    - Analyzing query patterns
    """
    
    def __init__(self, slow_query_threshold_ms: float = DEFAULT_SLOW_QUERY_THRESHOLD_MS):
        """
        Initialize the query profiler.
        
        Args:
            slow_query_threshold_ms: Threshold for slow queries in milliseconds
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.metrics: List[QueryMetrics] = []
        self.max_metrics = 1000  # Maximum number of metrics to store
        logger.info(f"Query profiler initialized with slow query threshold: {slow_query_threshold_ms}ms")
    
    def record_query(self, metrics: QueryMetrics) -> None:
        """
        Record query metrics.
        
        Args:
            metrics: Query metrics
        """
        # Log slow queries
        if metrics.is_slow(self.slow_query_threshold_ms):
            logger.warning(
                f"Slow query detected ({metrics.execution_time_ms:.2f}ms): {metrics.query}"
            )
        
        # Add to metrics list
        self.metrics.append(metrics)
        
        # Trim metrics list if needed
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """
        Get all recorded metrics.
        
        Returns:
            List[Dict[str, Any]]: List of metrics as dictionaries
        """
        return [metric.to_dict() for metric in self.metrics]
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """
        Get all slow queries.
        
        Returns:
            List[Dict[str, Any]]: List of slow query metrics as dictionaries
        """
        return [
            metric.to_dict() 
            for metric in self.metrics 
            if metric.is_slow(self.slow_query_threshold_ms)
        ]
    
    def get_average_execution_time(self) -> float:
        """
        Get average query execution time.
        
        Returns:
            float: Average execution time in milliseconds
        """
        if not self.metrics:
            return 0.0
        
        return sum(metric.execution_time_ms for metric in self.metrics) / len(self.metrics)
    
    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self.metrics.clear()


class ConnectionManager:
    """
    Database connection manager with connection pooling.
    
    This class provides:
    - Connection pooling
    - Session management
    - Connection health checks
    - Connection recycling
    """
    
    def __init__(
        self,
        connection_url: Optional[str] = None,
        pool_size: int = DEFAULT_POOL_SIZE,
        max_overflow: int = DEFAULT_MAX_OVERFLOW,
        pool_timeout: int = DEFAULT_POOL_TIMEOUT,
        pool_recycle: int = DEFAULT_POOL_RECYCLE
    ):
        """
        Initialize the connection manager.
        
        Args:
            connection_url: Database connection URL
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to allow beyond pool_size
            pool_timeout: Seconds to wait before giving up on getting a connection
            pool_recycle: Seconds after which a connection is recycled
        """
        self.connection_url = connection_url or settings.DATABASE_URL
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.connection_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # Check connection health before using
        )
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
        # Set up query profiling
        self.query_profiler = QueryProfiler()
        self._setup_query_profiling()
        
        logger.info(f"Connection manager initialized with pool size: {pool_size}")
    
    def _setup_query_profiling(self) -> None:
        """Set up query profiling events."""
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', time.time())
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info.pop('query_start_time')
            
            # Record metrics
            metrics = QueryMetrics(
                query=statement,
                parameters=parameters if not executemany else {},
                execution_time_ms=total_time * 1000,
                row_count=cursor.rowcount if cursor.rowcount > -1 else 0
            )
            
            self.query_profiler.record_query(metrics)
    
    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with connection_manager.session_scope() as session:
                session.add(some_object)
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """
        Get a new session.
        
        Returns:
            Session: A new SQLAlchemy session
        """
        return self.Session()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results as dictionaries
        """
        with self.session_scope() as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result]
    
    def check_connection(self) -> bool:
        """
        Check if the database connection is working.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the database connection.
        
        Returns:
            Dict[str, Any]: Connection information
        """
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "dialect": self.engine.dialect.name,
            "driver": self.engine.dialect.driver,
        }
    
    def close(self) -> None:
        """Close all connections in the pool."""
        self.engine.dispose()
        logger.info("Connection pool closed")


class QueryOptimizer:
    """
    Utility for optimizing database queries.
    
    This class provides:
    - Query analysis and optimization suggestions
    - Index recommendations
    - Query rewriting
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize the query optimizer.
        
        Args:
            connection_manager: Database connection manager
        """
        self.connection_manager = connection_manager
        self.engine = connection_manager.engine
        self.inspector = inspect(self.engine)
        logger.info("Query optimizer initialized")
    
    def analyze_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a query and provide optimization suggestions.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # Execute EXPLAIN
        explain_query = f"EXPLAIN ANALYZE {query}"
        
        try:
            with self.connection_manager.session_scope() as session:
                result = session.execute(text(explain_query), params or {})
                explain_output = [dict(row) for row in result]
            
            # Parse EXPLAIN output
            # This is PostgreSQL-specific and would need to be adapted for other databases
            analysis = self._parse_explain_output(explain_output)
            
            return {
                "query": query,
                "explain": explain_output,
                "analysis": analysis,
                "suggestions": self._generate_suggestions(analysis),
            }
        except SQLAlchemyError as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "query": query,
                "error": str(e),
                "suggestions": ["Could not analyze query due to error"],
            }
    
    def _parse_explain_output(self, explain_output: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse EXPLAIN output.
        
        Args:
            explain_output: EXPLAIN output
            
        Returns:
            Dict[str, Any]: Parsed analysis
        """
        # This is a simplified implementation
        # A real implementation would parse the EXPLAIN output in detail
        
        analysis = {
            "sequential_scans": 0,
            "index_scans": 0,
            "estimated_cost": 0,
            "estimated_rows": 0,
        }
        
        for row in explain_output:
            plan = str(row.get("QUERY PLAN", ""))
            
            if "Seq Scan" in plan:
                analysis["sequential_scans"] += 1
            
            if "Index Scan" in plan:
                analysis["index_scans"] += 1
            
            # Extract cost if available
            cost_match = re.search(r"cost=([0-9.]+)\.\.([0-9.]+)", plan)
            if cost_match:
                analysis["estimated_cost"] = float(cost_match.group(2))
            
            # Extract rows if available
            rows_match = re.search(r"rows=([0-9]+)", plan)
            if rows_match:
                analysis["estimated_rows"] = int(rows_match.group(1))
        
        return analysis
    
    def _generate_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate optimization suggestions based on analysis.
        
        Args:
            analysis: Query analysis
            
        Returns:
            List[str]: Optimization suggestions
        """
        suggestions = []
        
        if analysis["sequential_scans"] > 0:
            suggestions.append(
                "Query contains sequential scans, which can be slow for large tables. "
                "Consider adding appropriate indexes."
            )
        
        if analysis["estimated_cost"] > 1000:
            suggestions.append(
                f"Query has a high estimated cost ({analysis['estimated_cost']}). "
                "Consider simplifying the query or adding indexes."
            )
        
        if analysis["estimated_rows"] > 10000:
            suggestions.append(
                f"Query returns a large number of rows ({analysis['estimated_rows']}). "
                "Consider adding LIMIT or pagination."
            )
        
        return suggestions
    
    def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get indexes for a table.
        
        Args:
            table_name: Table name
            
        Returns:
            List[Dict[str, Any]]: List of indexes
        """
        return self.inspector.get_indexes(table_name)
    
    def recommend_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Recommend indexes for a table based on query patterns.
        
        Args:
            table_name: Table name
            
        Returns:
            List[Dict[str, Any]]: List of recommended indexes
        """
        # Get slow queries for this table
        slow_queries = [
            metric for metric in self.connection_manager.query_profiler.metrics
            if metric.is_slow() and table_name.lower() in metric.query.lower()
        ]
        
        # Get existing indexes
        existing_indexes = self.get_table_indexes(table_name)
        existing_columns = set()
        for idx in existing_indexes:
            existing_columns.update(idx["column_names"])
        
        # Analyze queries to find potential index candidates
        # This is a simplified implementation
        candidates = set()
        
        for metric in slow_queries:
            # Look for WHERE clauses
            where_match = re.search(r"WHERE\s+([^;]+)", metric.query, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1)
                
                # Extract column names (simplified)
                columns = re.findall(r"([a-zA-Z0-9_]+)\s*[=><]", where_clause)
                
                for col in columns:
                    if col.lower() not in [c.lower() for c in existing_columns]:
                        candidates.add(col)
        
        # Generate recommendations
        recommendations = []
        for column in candidates:
            recommendations.append({
                "table": table_name,
                "columns": [column],
                "reason": f"Frequently used in WHERE clauses of slow queries",
            })
        
        return recommendations


class BatchProcessor:
    """
    Utility for batch processing database operations.
    
    This class provides:
    - Efficient batch inserts
    - Batch updates
    - Batch deletes
    """
    
    def __init__(
        self, 
        connection_manager: ConnectionManager,
        batch_size: int = DEFAULT_BATCH_SIZE
    ):
        """
        Initialize the batch processor.
        
        Args:
            connection_manager: Database connection manager
            batch_size: Default batch size
        """
        self.connection_manager = connection_manager
        self.batch_size = batch_size
        logger.info(f"Batch processor initialized with batch size: {batch_size}")
    
    def batch_insert(
        self, 
        table: Table, 
        rows: List[Dict[str, Any]], 
        batch_size: Optional[int] = None
    ) -> int:
        """
        Insert rows in batches.
        
        Args:
            table: SQLAlchemy Table
            rows: Rows to insert
            batch_size: Batch size (defaults to self.batch_size)
            
        Returns:
            int: Number of rows inserted
        """
        if not rows:
            return 0
        
        batch_size = batch_size or self.batch_size
        total_inserted = 0
        
        # Process in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            with self.connection_manager.session_scope() as session:
                session.execute(table.insert(), batch)
                total_inserted += len(batch)
        
        logger.info(f"Batch inserted {total_inserted} rows into {table.name}")
        return total_inserted
    
    def batch_update(
        self, 
        table: Table, 
        updates: List[Dict[str, Any]], 
        id_column: str,
        batch_size: Optional[int] = None
    ) -> int:
        """
        Update rows in batches.
        
        Args:
            table: SQLAlchemy Table
            updates: Updates to apply (must include id_column)
            id_column: Primary key column name
            batch_size: Batch size (defaults to self.batch_size)
            
        Returns:
            int: Number of rows updated
        """
        if not updates:
            return 0
        
        batch_size = batch_size or self.batch_size
        total_updated = 0
        
        # Process in batches
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            with self.connection_manager.session_scope() as session:
                for item in batch:
                    if id_column not in item:
                        logger.warning(f"Skipping update: missing {id_column}")
                        continue
                    
                    id_value = item[id_column]
                    update_values = {k: v for k, v in item.items() if k != id_column}
                    
                    session.execute(
                        table.update().where(getattr(table.c, id_column) == id_value),
                        update_values
                    )
                    total_updated += 1
        
        logger.info(f"Batch updated {total_updated} rows in {table.name}")
        return total_updated
    
    def batch_delete(
        self, 
        table: Table, 
        ids: List[Any], 
        id_column: str,
        batch_size: Optional[int] = None
    ) -> int:
        """
        Delete rows in batches.
        
        Args:
            table: SQLAlchemy Table
            ids: IDs of rows to delete
            id_column: Primary key column name
            batch_size: Batch size (defaults to self.batch_size)
            
        Returns:
            int: Number of rows deleted
        """
        if not ids:
            return 0
        
        batch_size = batch_size or self.batch_size
        total_deleted = 0
        
        # Process in batches
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            
            with self.connection_manager.session_scope() as session:
                result = session.execute(
                    table.delete().where(getattr(table.c, id_column).in_(batch))
                )
                total_deleted += result.rowcount
        
        logger.info(f"Batch deleted {total_deleted} rows from {table.name}")
        return total_deleted


def cached_query(ttl: int = DEFAULT_CACHE_TTL, namespace: str = "db_queries"):
    """
    Decorator for caching database queries.
    
    Args:
        ttl: Cache TTL in seconds
        namespace: Cache namespace
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return func(*args, **kwargs)
            
            # Get cache
            cache = get_cache(namespace)
            
            # Generate cache key
            key = f"{func.__module__}.{func.__name__}:{hash(str(args))}-{hash(str(kwargs))}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        return wrapper
    
    return decorator


# Create global instances
connection_manager = ConnectionManager()
query_optimizer = QueryOptimizer(connection_manager)
batch_processor = BatchProcessor(connection_manager)


# Add SQLAlchemy event listeners for query optimization
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance."""
    if connection_manager.engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=30000000000")
        cursor.close()


@event.listens_for(Engine, "connect")
def set_postgresql_settings(dbapi_connection, connection_record):
    """Set PostgreSQL settings for better performance."""
    if connection_manager.engine.dialect.name == "postgresql":
        cursor = dbapi_connection.cursor()
        cursor.execute("SET work_mem = '50MB'")
        cursor.execute("SET maintenance_work_mem = '256MB'")
        cursor.execute("SET random_page_cost = 1.1")
        cursor.close()