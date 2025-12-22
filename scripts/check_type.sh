#!/bin/bash

for key in $(docker exec tso-redis redis-cli KEYS "sportsbook:*:metadata"); do
	type=$(docker exec tso-redis redis-cli TYPE "$key")
	echo "$key is type: $type"
done