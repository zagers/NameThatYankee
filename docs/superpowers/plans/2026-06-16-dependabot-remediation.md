# Dependabot Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 6 security vulnerabilities identified in transitive npm dependencies by configuring `overrides` in `package.json`.

**Architecture:** Enforce safe, patched versions of `tar`, `form-data`, `js-yaml`, `protobufjs`, and `ws` in the project's dependency tree via the npm `overrides` block.

**Tech Stack:** Node.js, npm, package.json

## Global Constraints

- Do not introduce breaking dependencies.
- All frontend Vitest and security rules tests must pass.
- No direct commit to master (create a fix/ branch).

---

### Task 1: Update package.json overrides and run npm install

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json` (via npm install)

**Interfaces:**
- Consumes: None
- Produces: Correctly overridden dependency lockfile.

- [ ] **Step 1: Add/update overrides in package.json**

Modify `package.json` to include the following inside the `"overrides"` block:
```json
  "overrides": {
    "flatted": "3.4.2",
    "@tootallnate/once": "3.0.1",
    "postcss": "8.5.10",
    "uuid": "14.0.0",
    "tar": "7.5.16",
    "form-data": "4.0.6",
    "js-yaml": "4.2.0",
    "protobufjs": "7.6.4",
    "ws": "7.5.11"
  }
```

- [ ] **Step 2: Run npm install**

Run: `npm install`
Expected: Lockfile updates successfully, and the 6 audit vulnerability warnings disappear.

- [ ] **Step 3: Run npm audit to verify clean report**

Run: `npm audit`
Expected: 0 vulnerabilities found.

- [ ] **Step 4: Commit changes**

```bash
git add package.json package-lock.json
git commit -m "fix: remediate dependabot vulnerabilities via package overrides"
```

---

### Task 2: Verify all frontend and security rules tests pass

**Files:**
- Modify: None

**Interfaces:**
- Consumes: Transitive dependency upgrades from Task 1.
- Produces: Green test verification of all JS frontend tests and Firebase security rules.

- [ ] **Step 1: Run frontend tests via npm**

Run: `npm test`
Expected: All Vitest and security rules tests pass successfully with the new package overrides in place.

- [ ] **Step 2: Commit any necessary test ledger updates**

```bash
git commit --allow-empty -m "test: verify overrides compatibility with firebase and vitest"
```
