# Operational SLO / SLI Spec
**Project:** WIT V2

## Overview
Service Level Objectives (SLOs) derived from the Non-Functional Requirements. Measurements are universally queried vs a Rolling 30d window, tracked via Datadog.

## Authoritative Data Sources
- **Live Match Logic / Network Latency:** Datadog APM traces ingested from ECS Go Nodes.
- **Crash Rates / Client Starts:** Sentry Mobile Client SDK events.
- **Push Emissions:** AWS SNS / APNs delivery receipt logs.

## Defined SLOs

### 1. Match Integrity
- **Live Match Completion Rate:** ≥ 99.5%
- **Definition:** Percentage of Live Matches terminating naturally without an unhandled server 5xx exception or forced pod eviction.
- **State Divergence (Desync) Rate:** ≤ 0.00%
- **Definition:** Any detected hash mismatch between client/server resulting in a desync modal counts as a P1 Breach immediately. Error budget is rigidly zero.

### 2. Performance (Latency)
- **Live Move Payload Validation:** p95 latency ≤ 150ms 
- **Definition:** Measured strictly from WebSocket ingress termination to egress flush via Go processing layer.
- **Client App Launch Time:** p95 < 2s cold start to lobby view globally.

### 3. Reliability
- **Push Notification Trigger Success:** ≥ 99.9% emission success downstream to APNs / FCM.
- **Crash-Free Sessions (Mobile):** ≥ 99.5% tracked via Sentry globally.
- **Reconnect Success Rate:** ≥ 95%
- **Definition:** Ratio of clients actively dropping a WebSocket that successfully reconstruct board parity within their grace window payload.

## Breach & Error Budget Policy
- Dropping below 99.5% on Crash-Free sessions or Match Completions automatically suspends all active Feature/Content engineering sprints. Development pivots 100% to stability remediation until the rolling 7d budget recovers the 30d slope.
