#!/bin/bash

DATE=$(date "+%Y-%m-%d")
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
ENV_NAME=${ENV_NAME:-"unknown"}

LOG="/var/log/monitor/health.log"
REPORT_DIR="/var/log/monitor/reports"
REPORT_FILE="$REPORT_DIR/$DATE-$ENV_NAME-report.txt"

mkdir -p "$REPORT_DIR"

TODAY_LOGS=$(grep "$DATE" "$LOG")

OK_COUNT=$(echo "$TODAY_LOGS" | grep -c "OK")
CRITICAL_COUNT=$(echo "$TODAY_LOGS" | grep -c "CRITICAL")

TOTAL=$((OK_COUNT + CRITICAL_COUNT))

if [ "$TOTAL" -eq 0 ]; then
    UPTIME=0
else
    UPTIME=$(echo "scale=2; ($OK_COUNT / $TOTAL) * 100" | bc)
fi

{
echo "=================================="
echo "Daily System Report - $DATE"
echo "Environment: $ENV_NAME"
echo "Generated: $TIMESTAMP"
echo "=================================="
echo "OK entries:       $OK_COUNT"
echo "CRITICAL entries: $CRITICAL_COUNT"
echo "Total checks:     $TOTAL"
echo "Uptime:           $UPTIME%"
echo "=================================="
} > "$REPORT_FILE"

echo "$TIMESTAMP - Daily report generated: $REPORT_FILE" >> "$LOG"
