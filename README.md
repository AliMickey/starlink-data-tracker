# Starlink Data Tracker
## Description
Community maintained database for Starlink data.

https://starlinktrack.com

![image](https://user-images.githubusercontent.com/60691199/206889964-3fc4651e-7e67-41b7-b845-299589c6a2e3.png)


## Features
### Firmware
Firmware, software, and hardware versions are collected for historical purpose. This allows us to compare and curate notes for each revision.

### Speedtests
Tracking the performance of any ISP is important for accountability, we make use of Speedtest.net's services to store results from users. Data is captured via the website form, the official [Discord](https://discord.gg/Rr2u4ystEe) channel and via user submitted results via the API. (Note: Ookla has stopped providing the country code in speedtest results, thus we need to maintain a separate list of city to country mappings in order to perform accurate result categorisation).

### Network
An easy way to check your IP address, Point of Presence and region. Complemented with a global rollout map of IPv4 & IPv6.

## Motivation
The existing [spreadsheet](https://docs.google.com/spreadsheets/d/1nsdLZ34VVX1qNVlDlAErzLov-fb_ZWgpYAQJWp_W8ic) solution was cumbersome and very messy.

## Technologies Used
[Flask](https://flask.palletsprojects.com),
[Bootstrap](https://getbootstrap.com),
[Docker](https://www.docker.com)
