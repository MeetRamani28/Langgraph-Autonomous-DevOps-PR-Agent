# Use the official pgvector image which comes with the extension pre-installed.
# This is simpler, faster, and more reliable than building it manually.
# The image is based on the official postgres image.
# See: https://hub.docker.com/r/pgvector/pgvector
FROM pgvector/pgvector:pg16
