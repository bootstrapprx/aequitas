---
type: phase
phase_id: "P7"
status: done
depends_on: []
owner: you
updated: 2025-12-28


## What it means
- AI agents for guidance, auditing, and automation.

## Status
- ✅ Done (Observer Mode)

## What's Done
- Dexter Observer (read-only advisory intelligence)
  - `/api/v1/dexter/observer` endpoints
  - Pattern detection (anomalies, trends, missing entries, account usage)
  - Read-only database role enforcement (Migration 035)
  - Mandatory disclaimer: "Read-only observations, advisory only"
  - Integrated into: Company Dashboard, Onboarding Wizard
  - DexterInsightsPanel and DexterSidebar UI components
- Sandbox Engine (tax simulation and scenario analysis)
  - `/api/v1/sandbox` endpoints
  - Isolated sandbox schema (Migration 033-034)
  - Scenario creation, projection binding, tax liability simulation
  - DexterSandboxObserver for scenario pattern analysis
- Fiscal Engine (tax calculation)
  - Tax profile management, tax runs, tax facts, tax positions
  - Consolidated tax calculations with deterministic recalculation
  - Disclaimer: "Estimated / Projected Tax Exposure"
- Organizer AI
  - Transaction classification with learning rules
  - AI-powered account mapping suggestions

## What's Missing
- Sandbox UI (backend is operational, no dedicated frontend dashboard)
- Dexter proactive recommendations (currently reactive/passive)
- Advanced AI workflows beyond Observer mode

## Goals
- [[GOAL — Sandbox UI]]
