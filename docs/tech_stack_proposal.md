# WIT V2 Tech Stack Proposal

## Overview
To deliver a responsive, server-authoritative, and scalable global multiplayer game with a V-Model approach, the technology stack prioritizes strict schemas, strong typing, real-time networking, and cross-platform delivery.

## 1. Client (Mobile Application)
**Framework: React Native (via Expo)**
- **Why:** Delivers rapid cross-platform deployment. 
- **Native Boundaries:** The project will initialize as Managed Expo. However, it is fully expected to migrate to `expo prebuild` (Continuous Native Generation) due to required custom native modules for deep-linking performance and advanced Sentry crash reporting.
- **Build Strategy:** EAS Build and EAS Submit will manage the CI/CD deployment pipeline to iOS/Android.
- **Animation Engine:** React Native Reanimated.
- **State Management:** Zustand for lightweight, scalable game UI state without Redux bloat.

## 2. Server (Backend Architecture)
**API & Meta Systems: Node.js (TypeScript)**
- **Why:** Perfect for handling REST APIs.
**Real-time Game Server: Go (Golang)**
- **Why:** Handles highly concurrent WebSocket connections efficiently, managing live match states with low latency.

*CRUCIAL BOUNDARY NOTE: Polyglot domain duplication must be avoided. A single canonical Protobuf repository will define all schemas and action definitions.*

## 3. Database Layer
**Primary Durable Data Store: PostgreSQL**
- **Purpose:** Relational mapping of User Profiles, LEDGER, Match Results, and Auth records.
**In-Memory Cache: Redis**
- **Purpose:** Managing ephemeral matchmaking queue assignments. Redis shall NOT act as an authoritative store for Live Game States (Live states should remain in application memory on Go nodes, snapshotted iteratively to Postgres).

## 4. Infrastructure & Hosting
**Cloud Provider: AWS**
- **Compute:** ECS (Elastic Container Service) configured over AWS Fargate for optimized operational speed and simplicity over Kubernetes overhead.
- **Network Ingress Routing:** 
  - Standard REST APIs: Amazon API Gateway -> Application Load Balancer (ALB).
  - WebSocket Go Servers: Network Load Balancer (NLB) to support direct persistent TCP/WS connections without HTTP polling degradation, avoiding standard API Gateway timeout limits.
- **Databases:** Amazon RDS (Postgres), Amazon ElastiCache (Redis).

## 5. Deployment, Observability, and Telemetry
- **Infrastructure as Code (IaC):** Terraform OR AWS CDK. Required for reproducible deployment.
- **Observability:** OpenTelemetry emitting to Datadog. Required for the NFR traces.
- **Crash/Error Reporting:** Sentry (Mobile & Backend context).
- **Feature Flags:** LaunchDarkly.
- **Secrets Management:** AWS Secrets Manager.
