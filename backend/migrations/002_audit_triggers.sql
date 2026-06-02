-- Audit Trail Triggers
-- These triggers automatically log all changes to critical tables

-- Function to log changes
CREATE OR REPLACE FUNCTION log_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        organization_id,
        user_id,
        action,
        entity_type,
        entity_id,
        old_values,
        new_values,
        created_at
    ) VALUES (
        COALESCE(NEW.organization_id, OLD.organization_id),
        COALESCE(NEW.created_by, OLD.created_by),
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        row_to_json(OLD),
        row_to_json(NEW)
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for projects
DROP TRIGGER IF EXISTS audit_projects ON projects;
CREATE TRIGGER audit_projects
    AFTER INSERT OR UPDATE OR DELETE ON projects
    FOR EACH ROW EXECUTE FUNCTION log_audit_trigger();

-- Create trigger for analysis_versions
DROP TRIGGER IF EXISTS audit_analysis_versions ON analysis_versions;
CREATE TRIGGER audit_analysis_versions
    AFTER INSERT OR UPDATE OR DELETE ON analysis_versions
    FOR EACH ROW EXECUTE FUNCTION log_audit_trigger();

-- Create trigger for rooms
DROP TRIGGER IF EXISTS audit_rooms ON rooms;
CREATE TRIGGER audit_rooms
    AFTER INSERT OR UPDATE OR DELETE ON rooms
    FOR EACH ROW EXECUTE FUNCTION log_audit_trigger();

-- Create trigger for boq_items
DROP TRIGGER IF EXISTS audit_boq_items ON boq_items;
CREATE TRIGGER audit_boq_items
    AFTER INSERT OR UPDATE OR DELETE ON boq_items
    FOR EACH ROW EXECUTE FUNCTION log_audit_trigger();

-- Create trigger for rate_cards
DROP TRIGGER IF EXISTS audit_rate_cards ON rate_cards;
CREATE TRIGGER audit_rate_cards
    AFTER INSERT OR UPDATE OR DELETE ON rate_cards
    FOR EACH ROW EXECUTE FUNCTION log_audit_trigger();

-- Create trigger for comments
DROP TRIGGER IF EXISTS audit_comments ON comments;
CREATE TRIGGER audit_comments
    AFTER INSERT OR UPDATE OR DELETE ON comments
    FOR EACH ROW EXECUTE FUNCTION log_audit_trigger();

-- Create trigger for approvals
DROP TRIGGER IF EXISTS audit_approvals ON approvals;
CREATE TRIGGER audit_approvals
    AFTER INSERT OR UPDATE OR DELETE ON approvals
    FOR EACH ROW EXECUTE FUNCTION log_audit_trigger();
