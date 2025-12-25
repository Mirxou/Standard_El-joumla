-- Migration 027: Optimize Security & Performance Indexes
-- Created: 2025-12-10
-- Description: Enhanced indexes for security tables and performance optimization

PRAGMA foreign_keys = ON;

-- ============================================================================
-- SECURITY EVENTS INDEXES (Phase 5.2)
-- ============================================================================

-- Composite index for common queries: event_type + timestamp
CREATE INDEX IF NOT EXISTS idx_security_events_type_timestamp 
ON security_events(event_type, timestamp DESC);

-- Composite index for user activity tracking
CREATE INDEX IF NOT EXISTS idx_security_events_user_timestamp 
ON security_events(user_id, timestamp DESC) WHERE user_id IS NOT NULL;

-- Composite index for severity filtering
CREATE INDEX IF NOT EXISTS idx_security_events_severity_timestamp 
ON security_events(severity, timestamp DESC);

-- Index for IP address tracking (for intrusion detection)
CREATE INDEX IF NOT EXISTS idx_security_events_ip_timestamp 
ON security_events(ip_address, timestamp DESC) WHERE ip_address IS NOT NULL;

-- Composite index for company isolation
CREATE INDEX IF NOT EXISTS idx_security_events_company_timestamp 
ON security_events(company_id, timestamp DESC) WHERE company_id IS NOT NULL;

-- ============================================================================
-- SECURITY THREATS INDEXES (Intrusion Detection)
-- ============================================================================

-- Composite index for threat type and level
CREATE INDEX IF NOT EXISTS idx_threats_type_level 
ON security_threats(threat_type, threat_level);

-- Composite index for IP and detection time
CREATE INDEX IF NOT EXISTS idx_threats_ip_detected 
ON security_threats(source_ip, detected_at DESC);

-- Index for blocked threats
CREATE INDEX IF NOT EXISTS idx_threats_blocked 
ON security_threats(blocked, detected_at DESC) WHERE blocked = 1;

-- Composite index for company isolation
CREATE INDEX IF NOT EXISTS idx_threats_company_detected 
ON security_threats(company_id, detected_at DESC) WHERE company_id IS NOT NULL;

-- ============================================================================
-- BLOCKED IPS INDEXES
-- ============================================================================

-- Index for active blocks (not expired)
CREATE INDEX IF NOT EXISTS idx_blocked_ips_active 
ON blocked_ips(ip_address, expires_at) WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP;

-- Index for expiration cleanup
CREATE INDEX IF NOT EXISTS idx_blocked_ips_expires 
ON blocked_ips(expires_at) WHERE expires_at IS NOT NULL;

-- Composite index for company isolation
CREATE INDEX IF NOT EXISTS idx_blocked_ips_company 
ON blocked_ips(company_id, blocked_at DESC) WHERE company_id IS NOT NULL;

-- ============================================================================
-- USER SESSIONS INDEXES (Enhanced)
-- ============================================================================

-- Composite index for active sessions lookup
CREATE INDEX IF NOT EXISTS idx_sessions_user_active 
ON user_sessions(user_id, is_active, last_activity DESC) WHERE is_active = 1;

-- Index for session cleanup (expired sessions)
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity 
ON user_sessions(last_activity) WHERE is_active = 1;

-- Composite index for IP tracking
CREATE INDEX IF NOT EXISTS idx_sessions_ip_active 
ON user_sessions(ip_address, is_active, login_time DESC) WHERE ip_address IS NOT NULL;

-- Index for session token lookup (if session_token column exists)
-- Note: This assumes session_token might be added later
-- CREATE INDEX IF NOT EXISTS idx_sessions_token 
-- ON user_sessions(session_token) WHERE session_token IS NOT NULL;

-- ============================================================================
-- SECURITY AUDIT LOG INDEXES (from security_service.py)
-- ============================================================================

-- Composite index for user activity audit
CREATE INDEX IF NOT EXISTS idx_security_audit_log_user_created 
ON security_audit_log(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Composite index for event type filtering
CREATE INDEX IF NOT EXISTS idx_security_audit_log_event_created 
ON security_audit_log(event_type, created_at DESC);

-- Index for IP address tracking
CREATE INDEX IF NOT EXISTS idx_security_audit_log_ip_created 
ON security_audit_log(ip_address, created_at DESC) WHERE ip_address IS NOT NULL;

-- ============================================================================
-- COMPLIANCE TABLES INDEXES (Phase 5.1)
-- ============================================================================

-- Compliance rules indexes
CREATE INDEX IF NOT EXISTS idx_compliance_rules_category_active 
ON compliance_rules(category, is_active) WHERE is_active = 1;

CREATE INDEX IF NOT EXISTS idx_compliance_rules_company_active 
ON compliance_rules(company_id, is_active) WHERE company_id IS NOT NULL AND is_active = 1;

-- Compliance checks indexes
CREATE INDEX IF NOT EXISTS idx_compliance_checks_rule_status 
ON compliance_checks(rule_id, status, check_date DESC);

CREATE INDEX IF NOT EXISTS idx_compliance_checks_company_date 
ON compliance_checks(company_id, check_date DESC) WHERE company_id IS NOT NULL;

-- ============================================================================
-- API PERFORMANCE INDEXES
-- ============================================================================

-- Index for API rate limiting (if api_rate_limits table exists)
-- CREATE INDEX IF NOT EXISTS idx_api_rate_limits_user_endpoint 
-- ON api_rate_limits(user_id, endpoint, window_start);

-- ============================================================================
-- GENERAL PERFORMANCE OPTIMIZATIONS
-- ============================================================================

-- Index for users table (if not exists)
CREATE INDEX IF NOT EXISTS idx_users_username_active 
ON users(username, is_active) WHERE is_active = 1;

CREATE INDEX IF NOT EXISTS idx_users_company_active 
ON users(company_id, is_active) WHERE company_id IS NOT NULL AND is_active = 1;

-- Index for companies table
CREATE INDEX IF NOT EXISTS idx_companies_active_default 
ON companies(is_active, is_default) WHERE is_active = 1;

-- ============================================================================
-- ANALYZE & OPTIMIZE
-- ============================================================================

-- Update query planner statistics
ANALYZE;

-- Rebuild indexes for optimal performance
-- Note: VACUUM will rebuild the entire database, use with caution in production
-- VACUUM;

-- ============================================================================
-- INDEX USAGE STATISTICS (for monitoring)
-- ============================================================================

-- Create a view to monitor index usage (SQLite 3.9+)
-- Note: SQLite doesn't have built-in index usage stats, but we can track manually
-- This is a placeholder for future monitoring

-- ============================================================================
-- NOTES
-- ============================================================================
-- 
-- 1. Composite indexes are ordered by selectivity (most selective first)
-- 2. DESC ordering is used for timestamp columns (most recent first)
-- 3. Partial indexes (WHERE clauses) reduce index size and improve performance
-- 4. Company isolation indexes support multi-tenant architecture
-- 5. Regular ANALYZE should be run after significant data changes
-- 6. Consider running VACUUM during maintenance windows
--
-- ============================================================================

