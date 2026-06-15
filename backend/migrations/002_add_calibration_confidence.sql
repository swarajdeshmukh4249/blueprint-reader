-- Add confidence fields to scale_calibrations table
ALTER TABLE scale_calibrations 
ADD COLUMN confidence_score DECIMAL(5, 3),
ADD COLUMN confidence_level VARCHAR(20),
ADD COLUMN confidence_badge JSONB,
ADD COLUMN confidence_warnings JSONB,
ADD COLUMN confidence_factors JSONB;

-- Add index for confidence level queries
CREATE INDEX idx_scale_calibrations_confidence ON scale_calibrations(confidence_level);
