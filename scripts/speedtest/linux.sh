#!/bin/bash
speedtestUrl=$(./speedtest -f json | jq -r '.result.url')
apiKey=()
curl -X POST --form "api-key=$apiKey" --form "urls=$speedtestUrl" https://starlinktrack.com/speedtests/add
