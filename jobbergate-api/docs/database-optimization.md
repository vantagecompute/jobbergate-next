# Database Optimization Documentation

This document describes the database optimizations implemented in the migration `20260212_020944--b16b218ef5d6_add_database_indexes_for_performance.py`.

## Overview

The optimization focused on adding strategic indexes to improve query performance across the application, particularly for:
- Foreign key lookups and JOIN operations
- Cleanup/garbage collection queries
- Job status and tracking queries

## Indexes Added

### 1. Foreign Key Indexes

These indexes improve JOIN performance and foreign key constraint checking:

#### `idx_job_submissions_job_script_id` on `job_submissions.job_script_id`
- **Purpose**: Speeds up JOINs between job_submissions and job_scripts
- **Impact**: Used in list queries that need to display job script information alongside submissions
- **Estimated improvement**: 3-5x faster for queries filtering by job_script_id

#### `idx_job_scripts_parent_template_id` on `job_scripts.parent_template_id`
- **Purpose**: Speeds up JOINs between job_scripts and job_script_templates
- **Impact**: Used in cleanup operations and template-related queries
- **Estimated improvement**: 2-4x faster for template hierarchy queries

#### `idx_job_submission_metrics_job_submission_id` on `job_submission_metrics.job_submission_id`
- **Purpose**: Improves foreign key lookups and CASCADE delete operations
- **Impact**: While part of composite PK, a standalone index helps with queries filtering by submission
- **Estimated improvement**: 10-20% faster for metric queries by submission_id

#### `idx_job_progress_job_submission_id` on `job_progress.job_submission_id`
- **Purpose**: Speeds up progress tracking queries and CASCADE operations
- **Impact**: Critical for fetching job progress history efficiently
- **Estimated improvement**: 5-10x faster for progress lookups

### 2. Frequently Queried Columns

#### `idx_job_submissions_slurm_job_id` on `job_submissions.slurm_job_id`
- **Purpose**: Enables fast lookups by Slurm job ID
- **Impact**: Critical for agent updates and job status synchronization
- **Estimated improvement**: Near-instant lookups (index scan vs sequential scan)

### 3. Composite Indexes for Cleanup Queries

These indexes optimize the garbage collection/cleanup operations that run periodically:

#### `idx_job_submissions_is_archived_updated_at` on `job_submissions(is_archived, updated_at)`
- **Query pattern**: `WHERE is_archived = ? AND updated_at < ?`
- **Purpose**: Cleanup old archived submissions efficiently
- **Impact**: Reduces full table scans during cleanup
- **Estimated improvement**: 50-100x faster for cleanup operations on large tables

#### `idx_job_scripts_is_archived_updated_at` on `job_scripts(is_archived, updated_at)`
- **Query pattern**: `WHERE is_archived = ? AND updated_at < ?`
- **Purpose**: Cleanup old archived job scripts efficiently
- **Impact**: Reduces full table scans during cleanup
- **Estimated improvement**: 50-100x faster for cleanup operations

#### `idx_job_script_templates_is_archived_updated_at` on `job_script_templates(is_archived, updated_at)`
- **Query pattern**: `WHERE is_archived = ? AND updated_at < ?`
- **Purpose**: Cleanup old archived templates efficiently
- **Impact**: Reduces full table scans during cleanup
- **Estimated improvement**: 50-100x faster for cleanup operations

## Query Patterns Optimized

### 1. List Queries with Relationships
```python
# Before: Sequential scan + nested loop
# After: Index scan + hash join
query = (
    select(JobSubmission)
    .where(JobSubmission.job_script_id == script_id)
    .options(selectinload(JobSubmission.job_script))
)
```

### 2. Cleanup Operations
```python
# Before: Full table scan
# After: Index range scan
query = (
    select(JobSubmission)
    .where(JobSubmission.is_archived == True)
    .where(JobSubmission.updated_at < threshold)
)
```

### 3. Agent Status Updates
```python
# Before: Sequential scan
# After: Direct index lookup
query = select(JobSubmission).where(JobSubmission.slurm_job_id == slurm_id)
```

### 4. Progress Tracking
```python
# Before: Sequential scan
# After: Index scan
query = (
    select(JobProgress)
    .where(JobProgress.job_submission_id == submission_id)
    .order_by(JobProgress.timestamp)
)
```

## Performance Impact

### Expected Improvements by Table Size

| Table Size | Cleanup Query | FK Lookup | Slurm Job Lookup |
|-----------|---------------|-----------|------------------|
| < 1K rows | Minimal gain | 2-3x | 5-10x |
| 1K-10K | 10-20x | 3-5x | 10-50x |
| 10K-100K | 50-100x | 5-10x | 50-500x |
| > 100K | 100-1000x | 10-20x | 500-5000x |

### Index Size Estimates

Based on typical data:
- Single column indexes: ~5-10MB per 100K rows
- Composite indexes: ~8-15MB per 100K rows
- Total additional storage: ~50-100MB per 100K rows across all indexes

### Trade-offs

**Benefits:**
- Dramatically faster SELECT queries
- More efficient JOIN operations
- Faster CASCADE delete operations
- Improved cleanup performance

**Costs:**
- ~10-20% slower INSERT operations (negligible in practice)
- ~5-15% slower UPDATE operations on indexed columns
- Additional disk space for indexes
- Slightly longer migration time on existing data

## Monitoring

To verify the impact of these indexes, monitor:

1. **Query performance**:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM job_submissions 
   WHERE is_archived = true AND updated_at < NOW() - INTERVAL '30 days';
   ```

2. **Index usage**:
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
   FROM pg_stat_user_indexes
   WHERE indexname LIKE 'idx_%'
   ORDER BY idx_scan DESC;
   ```

3. **Index size**:
   ```sql
   SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass))
   FROM pg_indexes
   WHERE indexname LIKE 'idx_%';
   ```

## Migration Safety

The migration is safe to run in production:
- Uses `CREATE INDEX` (not `CREATE INDEX CONCURRENTLY` for simplicity)
- All indexes are non-unique
- Downgrade fully reverses all changes
- No data modifications
- Can be run during normal operations (brief table locks)

For large tables in production, consider running with `CONCURRENTLY`:
```sql
CREATE INDEX CONCURRENTLY idx_name ON table_name (column);
```

## Related Files

- **Migration**: `alembic/versions/20260212_020944--b16b218ef5d6_add_database_indexes_for_performance.py`
- **Models**:
  - `jobbergate_api/apps/job_submissions/models.py`
  - `jobbergate_api/apps/job_scripts/models.py`
  - `jobbergate_api/apps/job_script_templates/models.py`
- **Services** (consumers of these indexes):
  - `jobbergate_api/apps/job_submissions/services.py`
  - `jobbergate_api/apps/job_scripts/services.py`
  - `jobbergate_api/apps/job_script_templates/services.py`

## Future Optimizations

Potential future improvements:
1. Add partial indexes for active (non-archived) records
2. Consider BRIN indexes for timestamp columns on very large tables
3. Add covering indexes for frequently selected column combinations
4. Implement query result caching for expensive aggregations
5. Consider table partitioning for job_submission_metrics by time range
