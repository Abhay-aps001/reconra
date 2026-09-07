# Tasks 21–23 Frontend Product Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local run history and exports, inspected imports, Razorpay Test Mode sync, and methodology using the existing authoritative run lifecycle.

**Architecture:** `RunProvider.accept()` validates a public `RunResult` then persists a sanitized browser snapshot without blocking the live flow. Every new route delegates successful backend runs to that same `accept` path. Local snapshots are read-only fallback state; only live runs can decide exceptions or export backend artifacts.

**Stack:** Next.js App Router, React, native IndexedDB, native form controls, existing typed API client, Playwright and node:test.

## File ownership

- `apps/web/lib/storage/runs.ts`: schema-1 public snapshot persistence, validation, ordering, and pruning.
- `apps/web/features/reconciliation/run-controller.tsx`: sole authoritative acceptance and snapshot write; live/saved-only state.
- `apps/web/features/reconciliation/export-menu.tsx`: byte-preserving live artifact downloads.
- `apps/web/features/runs/run-history.tsx`: saved snapshot listing, opening, and deletion.
- `apps/web/features/imports/*`: parsed inspection response, multipart inspect, confirmation, validation, reconciliation UI.
- `apps/web/features/razorpay/sync-panel.tsx`: read-only Test Mode sync.
- `apps/web/app/{runs,import,razorpay,methodology}/page.tsx`: route composition only.
- `UX-CONTRACT.md`: durable navigation, local snapshot, async feedback, and deletion behavior.

## Tasks

- [ ] Write failing unit tests for sanitized snapshot validation, newest-first ordering, duplicate update, pruning, deletion, corruption skipping, and unavailable storage.
- [ ] Implement the IndexedDB repository and connect `accept` as the only persistence boundary.
- [ ] Write failing route/browser coverage for history and byte-preserving exports, then add Runs and export UI.
- [ ] Write failing import parser/API/browser coverage, then implement inspect → mapping confirmation → validate → reconcile.
- [ ] Write failing Razorpay/methodology browser coverage, then implement Test Mode sync and factual methodology route.
- [ ] Verify at 1440px, 768px, and 320px; run unit, lint, TypeScript, production build, serial Playwright, and diff checks.
