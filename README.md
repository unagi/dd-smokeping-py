# dd-smokeping-py
Dadadog multi-target fping like smokeping

## requirements
- fping(command)

## Installation
1. Install fping command
2. Copy the files from this github repo to your host

```
  fping.py -> /etc/dd-agent/checks.d
  fping.yaml -> /etc/dd-agent/conf.d
```

## Metric Description
- ping.rtt(histograms) : ping rtt from datadog agent to targets(fping.yaml)
- ping.total_cnt : total count of ping
- ping.loss_cnt : packet loss count of ping
