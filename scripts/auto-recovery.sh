#!/bin/bash

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
ENV_NAME=${ENV_NAME:-"unknown"}
CONTAINER_NAME="${ENV_NAME}-app"
LOG="/var/log/monitor/health.log"
RECOVERY_LOG="/var/log/monitor/recovery.log"

mkdir -p /var/log/monitor

STATUS="OK"

# Check 1 — Is the container running?
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    STATUS="CRITICAL"
    echo "$TIMESTAMP - CRITICAL - Container $CONTAINER_NAME is DOWN" >> $LOG
    echo "$TIMESTAMP - ACTION - Restarting $CONTAINER_NAME" >> $RECOVERY_LOG

    if docker start "$CONTAINER_NAME"; then
        echo "$TIMESTAMP - RECOVERY - $CONTAINER_NAME restarted successfully" >> $RECOVERY_LOG
    else
        echo "$TIMESTAMP - FAILED - Could not restart $CONTAINER_NAME" >> $RECOVERY_LOG
    fi
fi

# Check 2 — Is Nginx running?
if ! systemctl is-active --quiet nginx; then
    STATUS="CRITICAL"
    echo "$TIMESTAMP - CRITICAL - Nginx is DOWN" >> $LOG
    echo "$TIMESTAMP - ACTION - Restarting Nginx" >> $RECOVERY_LOG

    if systemctl restart nginx; then
        echo "$TIMESTAMP - RECOVERY - Nginx restarted successfully" >> $RECOVERY_LOG
    else
        echo "$TIMESTAMP - FAILED - Could not restart Nginx" >> $RECOVERY_LOG
    fi
fi


# Check 3 — Does the app respond?
if ! curl -sf http://localhost > /dev/null; then
    STATUS="CRITICAL"
    echo "$TIMESTAMP - CRITICAL - App is NOT responding on port 80" >> $LOG
    echo "$TIMESTAMP - ACTION - Restarting $CONTAINER_NAME" >> $RECOVERY_LOG

    if docker restart "$CONTAINER_NAME"; then
        echo "$TIMESTAMP - RECOVERY - $CONTAINER_NAME restarted successfully" >> $RECOVERY_LOG
    else
        echo "$TIMESTAMP - FAILED - Could not restart $CONTAINER_NAME" >> $RECOVERY_LOG
    fi
fi


if [ "$STATUS" = "OK" ]; then
    echo "$TIMESTAMP - OK - ENV=$ENV_NAME all systems up" >> $LOG
fi