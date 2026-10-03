#!/bin/bash

set -euo pipefail


# ---------------------------------------------------------
# Log cloud-init/user-data output
# ---------------------------------------------------------

exec > >(tee /var/log/cloudpulse-user-data.log | logger -t cloudpulse-user-data -s 2>/dev/console) 2>&1


echo "=========================================="
echo "CloudPulse EC2 bootstrap starting"
echo "=========================================="


# ---------------------------------------------------------
# System packages
#
# Amazon Linux 2023 already provides curl-minimal,
# so do NOT request the full curl package.
# ---------------------------------------------------------

dnf update -y

dnf install -y \
    docker \
    git


# ---------------------------------------------------------
# Start Docker
# ---------------------------------------------------------

systemctl enable docker

systemctl start docker


# Allow ec2-user to use Docker after reconnecting
usermod -aG docker ec2-user


# ---------------------------------------------------------
# Install Docker Compose plugin
# ---------------------------------------------------------

mkdir -p /usr/local/lib/docker/cli-plugins

curl -fL \
    "https://github.com/docker/compose/releases/download/v5.5.1/docker-compose-linux-x86_64" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose

chmod +x \
    /usr/local/lib/docker/cli-plugins/docker-compose


docker compose version


# ---------------------------------------------------------
# Add swap to help the small EC2 instance build Docker
# ---------------------------------------------------------

if ! swapon --show | grep -q "/swapfile"; then

    fallocate -l 2G /swapfile

    chmod 600 /swapfile

    mkswap /swapfile

    swapon /swapfile

    echo "/swapfile swap swap defaults 0 0" >> /etc/fstab

fi


# ---------------------------------------------------------
# Clone CloudPulse
# ---------------------------------------------------------

rm -rf /opt/CloudPulse

git clone \
    "${github_repo}" \
    /opt/CloudPulse


cd /opt/CloudPulse


# ---------------------------------------------------------
# Create production/demo environment file
# ---------------------------------------------------------

cat > .env <<'EOF'
POSTGRES_DB=${db_name}
POSTGRES_USER=${db_user}
POSTGRES_PASSWORD=${db_password}
EOF


chmod 600 .env


# ---------------------------------------------------------
# Build CloudPulse Docker image
# ---------------------------------------------------------

docker build \
    -t cloudpulse:latest \
    .


# ---------------------------------------------------------
# Start PostgreSQL first
# ---------------------------------------------------------

docker compose up -d postgres


# ---------------------------------------------------------
# Wait until PostgreSQL is ready
# ---------------------------------------------------------

for i in $(seq 1 30); do

    if docker compose exec -T postgres \
        pg_isready \
        -U "${db_user}" \
        -d "${db_name}" \
        >/dev/null 2>&1; then

        echo "PostgreSQL is ready."

        break

    fi


    echo "Waiting for PostgreSQL..."

    sleep 2

done


# ---------------------------------------------------------
# Initialize database schema
# ---------------------------------------------------------

docker compose run \
    --rm \
    app \
    python -m backend.database.init_db


# ---------------------------------------------------------
# Start CloudPulse application
# ---------------------------------------------------------

docker compose up -d app


# ---------------------------------------------------------
# Display final state
# ---------------------------------------------------------

docker compose ps


echo "=========================================="
echo "CloudPulse bootstrap completed"
echo "=========================================="