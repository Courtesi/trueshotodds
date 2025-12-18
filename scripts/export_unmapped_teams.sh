#!/bin/bash
# Extract unmapped teams from Docker logs and export to JSONL format
# Run this when you want to update team name mappings

set -e

OUTPUT_FILE="logs/unmapped_teams.jsonl"

echo "Extracting unmapped teams from Docker logs..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Extract unmapped team logs from all containers
# Filter for "Unmapped team:" lines, parse the key-value format
docker compose logs --no-log-prefix 2>/dev/null | \
    grep "Unmapped team:" | \
    awk -F'Unmapped team: ' '{print $2}' | \
    while IFS= read -r line; do
        # Parse the structured log format: league=X team="Y" book=Z context=W count=N
        league=$(echo "$line" | sed -n 's/.*league=\([^ ]*\).*/\1/p')
        team=$(echo "$line" | sed -n 's/.*team="\([^"]*\)".*/\1/p')
        book=$(echo "$line" | sed -n 's/.*book=\([^ ]*\).*/\1/p')
        context=$(echo "$line" | sed -n 's/.*context=\([^ ]*\).*/\1/p')
        count=$(echo "$line" | sed -n 's/.*count=\([0-9]*\).*/\1/p')

        # Create JSON entry (compatible with name_resolver.py)
        if [ -n "$team" ] && [ -n "$league" ]; then
            echo "{\"book\":\"$book\",\"league\":\"$league\",\"team_name\":\"$team\",\"context\":\"$context\",\"count\":$count,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
        fi
    done > "$OUTPUT_FILE"

# Count results
line_count=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')

if [ "$line_count" -eq 0 ]; then
    echo "✗ No unmapped teams found in Docker logs"
    echo "  Either:"
    echo "    - No teams are unmapped (good!)"
    echo "    - Logs don't span a full hour yet (wait for hourly batch)"
    rm -f "$OUTPUT_FILE"
else
    echo "✓ Exported $line_count unmapped team entries to $OUTPUT_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Run: uv run python -m arbfinder.utils.name_resolver"
    echo "  2. Add team name mappings interactively"
    echo "  3. Commit updated JSON files"
    echo "  4. Rebuild containers: docker compose build"
fi