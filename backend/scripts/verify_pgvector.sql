-- Verification script for pgvector installation
-- Run this to confirm pgvector is installed and working

-- 1. Check if extension is installed
SELECT
    extname as extension_name,
    extversion as version
FROM pg_extension
WHERE extname = 'vector';

-- Expected output: Should show 'vector' with a version number

-- 2. Test vector type works
-- This creates a temporary table with a vector column
CREATE TEMPORARY TABLE test_vector (
    id serial PRIMARY KEY,
    embedding vector(768)
);

-- Insert a test vector
INSERT INTO test_vector (embedding)
VALUES (ARRAY[0.1, 0.2, 0.3]::real[]::vector(768));

-- Query the test vector
SELECT id, vector_dims(embedding) as dimensions
FROM test_vector;

-- Expected output: Should show id=1, dimensions=768

-- Cleanup
DROP TABLE test_vector;

-- 3. Summary
SELECT
    'pgvector is installed and working correctly!' as status,
    extversion as version
FROM pg_extension
WHERE extname = 'vector';
