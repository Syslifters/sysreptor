#!/bin/bash
set -e  # exit on error
set -o pipefail  # fail pipeline if any command fails

# PostgreSQL Migration Script for SysReptor
# This script migrates the PostgreSQL database to a new version

# Default target version
TARGET_VERSION="${1:-18}"
BACKUP_DIR="$(pwd)/upgrade_postgres_backup$(date -Iseconds | tr -d ':')"


# Check preconditions
if [ ! -d "deploy" ]; then
    echo "Error: deploy/ directory not found. Please run this script from the SysReptor root directory." >&2
    exit 1
fi
cd deploy
if [ ! -f ".env" ]; then
    echo "Error: deploy/.env not found." >&2
    exit 1
fi

# Get current version
source ./.env
CURRENT_VERSION="${SYSREPTOR_POSTGRES_VERSION:-14}"

# Check if already on target version
if [ "$CURRENT_VERSION" = "$TARGET_VERSION" ]; then
    echo "Already running PostgreSQL version ${TARGET_VERSION}. No migration needed."
    exit 0
fi


# Confirm with user
echo ""
echo "WARNING: This will migrate your PostgreSQL database from version ${CURRENT_VERSION} to ${TARGET_VERSION}."
echo "This process will:"
echo "  1. Stop all SysReptor services"
echo "  2. Create a backup of your current database volume"
echo "  3. Upgrade PostgreSQL volume"
echo "  4. Restart SysReptor services"
echo ""
printf "Do you want to continue? [y/N]: "
read -r CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Migration cancelled."
    trap - EXIT  # disable error trap
    exit 0
fi


echo "Stopping SysReptor services..."
docker compose down


echo "Creating backup of current PostgreSQL data volume..."
mkdir -p "${BACKUP_DIR}"
cp .env "${BACKUP_DIR}/.env"
docker run \
    --rm \
    --volume="sysreptor-db-data:/data" \
    --volume="${BACKUP_DIR}:/backup" \
    "postgres:${CURRENT_VERSION}" \
    tar -czf /backup/pgdata.tar.gz -C /data .


echo "Upgrading postgres volume data..."
PGAUTOUPGRADE_LOGFILE="${BACKUP_DIR}/pgautoupgrade.log"
echo "Logging pgautoupgrade output to ${PGAUTOUPGRADE_LOGFILE}"
docker run \
    --rm \
    --volume="sysreptor-db-data:/data" \
    --env="POSTGRES_USER=${POSTGRES_USER:-reportcreator}" \
    --env="POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-reportcreator}" \
    --env="POSTGRES_DB=${POSTGRES_NAME:-reportcreator}" \
    --env="PGDATA=/data" \
    --env="PGAUTO_ONESHOT=yes" \
    "pgautoupgrade/pgautoupgrade:${TARGET_VERSION}-debian" 2>&1 | tee "${PGAUTOUPGRADE_LOGFILE}"
echo ""
echo "pgautoupgrade logfile: ${PGAUTOUPGRADE_LOGFILE}"
echo ""

echo "Updating .env with PostgreSQL version ${TARGET_VERSION}..."
if grep -qE "^[[:space:]]*(#[[:space:]]*)?SYSREPTOR_POSTGRES_VERSION" .env; then
    # Replace existing line (commented or uncommented)
    sed -i "s/^[[:space:]]*#\?[[:space:]]*SYSREPTOR_POSTGRES_VERSION.*/SYSREPTOR_POSTGRES_VERSION=${TARGET_VERSION}/" .env
else
    # Append if doesn't exist
    echo "SYSREPTOR_POSTGRES_VERSION=${TARGET_VERSION}" >> .env
fi
echo "Updated .env file"


echo "Starting SysReptor services..."
docker compose up -d
echo ""
echo "PostgreSQL migration to version ${TARGET_VERSION} completed successfully."

