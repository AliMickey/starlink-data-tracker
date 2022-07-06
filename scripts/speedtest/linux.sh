#!/bin/bash
speedtestUrl=$(./speedtest -f json  | jq -r '.result.url')
curl -X POST --form "source=script-official" --form "url=$speedtestUrl" https://starlinkversions.com/speedtests/add