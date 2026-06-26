#!/bin/bash

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
ENV_NAME=${ENV_NAME:-"unknown"}
HEALTH_LOG="/var/log/monitor/health.log"
ALERT_LOG="/var/log/monitor/alerts.log"

mkdir -p /var/log/monitor

# Get logs from last 10 minutes using timestamp comparison
RECENT_LOGS=$(awk -v date="$(date --date='10 minutes ago' '+%Y-%m-%d %H:%M:%S')" \
    '$0 >= date' "$HEALTH_LOG" 2>/dev/null)

# Count CRITICAL entries in recent logs
CRITICAL_COUNT=$(echo "$RECENT_LOGS" | grep -c "CRITICAL")

# Trigger alert if more than 3 CRITICALs in last 10 minutes
if [ "$CRITICAL_COUNT" -gt 3 ]; then
    echo "$TIMESTAMP - ALERT - ENV=$ENV_NAME - $CRITICAL_COUNT critical events in last 10 minutes" >> "$ALERT_LOG"
fi