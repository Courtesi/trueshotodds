#!/bin/bash

for key in $(docker exec tso-redis redis-cli KEYS "sportsbook:*:metadata"); do
	echo "Key: $key"
	docker exec tso-redis redis-cli HGETALL "$key" | paste -d': ' - -
	echo ""
done