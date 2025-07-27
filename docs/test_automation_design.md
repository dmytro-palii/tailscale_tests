# Overview

This design document complements the high-level README by capturing the in-depth test automation architecture, 
detailed platform flows, tool rationales, and scheduling strategies that don’t belong in a user-focused README. 
Use this as the single source of truth for our automation design decisions.


## Architecture Overview

Our test automation architecture treats Tailscale as an end-user client and is composed of these logical layers:

1. **CI/CD Orchestrator (GitHub Actions)**
   - Workflows for PR validation, nightly regression (02:00 AM CT), and manual dispatch.
   - Matrix jobs on `ubuntu-latest`, `macos-latest`, and `windows-latest` runners.

2. **Test Runners & Environments**
   - **macOS/iOS**: Hosted macOS runners (ARM/Intel) or cloud macOS VMs with Homebrew/App Store install.
   - **Windows**: `windows-latest` runners; dedicated agents with WinAppDriver.
   - Each runner provisions:
     - Python venv with all dependencies (`pytest`, `playwright`, `requests`, `pydantic`).
     - Tailscale client via end-user installer (Homebrew or MSI).
     - Appium server for iOS UI automation; WinAppDriver for Windows UI.

3. **Test Harness & Fixtures**
   - **pytest** orchestrates all tests.
   - `conftest.py` defines fixtures:
     - `tailscale_client`: ensures the client is at the desired state (up/down, exit node, routes).
     - `network_mesh`: shares peer IPs across runners via MagicDNS hostnames.
   - **LocalAPI/CLI**:
     - Use `requests` to call `http://localhost:41112/localapi/v0/...`.
     - Use `subprocess` to invoke `tailscale status`, `tailscale up`, etc.
   - **Page Objects**:
     - Encapsulate UI actions for installation screens, SSO login, and system-tray toggles.

4. **Network Mesh Configuration**
   - All runners join a shared tailnet managed externally (no admin API).
   - DERP for NAT traversal; MagicDNS resolves hostnames like `runner1.tailnet.test`.
   - Manual or scripted CLI setup in workflow jobs to configure exit nodes and routes.

5. **Reporting & Telemetry**
   - **Allure** (`allure-pytest`) generates interactive HTML reports and attachments (screenshots, logs).
   - **Slack Notifications** via webhook on failure or flakiness alerts.
   - **Grafana Dashboards** ingest JUnit XML metrics from CI to track pass rates and durations.
   - CI artifacts store the `reports/` directory for post-run analysis.

6. **Constraints & Alternative Meshes**
   - **End-User Only**: No use of Tailscale’s admin/control-plane APIs; tests treat client as a black box.
   - **Alternatives for Full Control**:
     - **Headscale**: Self-hosted control plane to spin up ephemeral tailnets under test orchestration.
     - **WireGuard** or **Nebula**: Simpler mesh VPN solutions to simulate connectivity for flows requiring admin access.


# Test Automation Design Document

## 1. What functionality are you testing? (Functionality under test)  
### 1.1 macOS / iOS
- Installation & SSO login (App Store/Homebrew + OAuth2)
- LocalAPI status check & token refresh
- WireGuard P2P connectivity with DERP fallback
- MagicDNS hostname resolution for peers
- Exit node enable/disable and routing validation
- Subnet route advertisement & resource access
- ACL enforcement (ping/SSH) and policy validation
- Taildrop file transfer tests
- Funnel service exposure tests
- Telemetry & log retrieval via LocalAPI

### 1.2 Windows
- MSI/EXE installation & SSO login (Windows Hello + browser OAuth2)
- System tray UI interactions (connect/disconnect, status)
- WireGuard interface creation, route table & firewall rule validation
- MagicDNS resolution of peer hostnames
- Exit node toggle via UI and `tailscale.exe up --exit-node` CLI
- Subnet route advertisement (`--advertise-routes`) & behind-the-scenes routing
- ACL enforcement tests (PowerShell SSH attempts, ICMP ping)
- Taildrop CLI file transfer tests
- LocalAPI status and logs retrieval via `tailscale status` & HTTP endpoint

## 2. What tools do you use to write and track the tests, and why? (Test authoring & tracking)

- **Unit Tests:**  
  - Framework: `pytest` (Python 3.8+).  
  - Purpose: fast, isolated logic validation (e.g., parsing LocalAPI responses).

- **API / Integration Tests:**  
  - Framework: `pytest` + `requests`.  
  - Validation: response schemas via `pydantic` models.  
  - Purpose: end-to-end LocalAPI and CLI flows (e.g., onboarding, status).

- **UI Tests:**  
  - macOS/iOS: Appium-Python-Client with XCUITest backend.  
  - Windows: WinAppDriver via `webdriver-manager`.  
  - Purpose: verify install/login flows and system-tray interactions.

- **Network / E2E Tests:**  
  - Framework: `pytest` + subprocess calls to `tailscale` CLI and `wireguard-tools`.  
  - Purpose: mesh connectivity, DNS resolution, exit-node routing.

- **Test Management:**  
  - System: JIRA + Xray.  
  - Rationale: integrates with dev workflows, supports BDD, traceability from requirements → tests → defects.

## 3. What tools do you use to communicate test success or failure, and why? (Result reporting & alerting)

- **HTML Reports:**  
  - Tool: Allure (`allure-pytest` plugin).  
  - Rationale: interactive, easy-to-navigate test result dashboards with step-by-step details.

- **CI Artifacts & Badges:**  
  - GitHub Actions uploads JUnit/XML and Allure artifacts; status badges shown in the repo README.  
  - Rationale: quick visual feedback on build health.

- **Chat Notifications:**  
  - Channel: Slack via incoming webhooks.  
  - Triggers: PR failures, nightly regression failures, and flaky-test alerts.  
  - Rationale: real-time visibility for the team.

- **Monitoring Dashboards:**  
  - Tool: Grafana (ingesting CI metrics).  
  - Metrics: pass rate, test durations, failure trends, flakiness rate.  
  - Rationale: long-term trend analysis and reliability tracking.

## 4. How do you identify which tests to automate? (Test selection strategy)

- **Core Business Impact:** Automate flows critical to user connectivity (onboarding, ACL enforcement) first.  
- **High Frequency:** Prioritize features exercised in every session (status polling, DNS resolution).  
- **Risk & Complexity:** Target error-prone or security-sensitive areas (token refresh, DERP fallback) early.  
- **ROI Analysis:** Automate scenarios where manual testing exceeds 5 man-hours/month.  
- **Stability Threshold:** Delay automating highly unstable or frequently changing features until they stabilize.

## 5. How did you select tests that you would not automate? (Tests you exclude)

- **UX Exploratory Tests:** Manual usability and layout reviews (e.g., interface smoothness, language localization)—best validated by human testers.  
- **Hardware Variability:** Physical network edge cases (e.g., cellular brown-outs, Wi-Fi interference) that are impractical to reliably simulate in automation.  
- **Performance at Scale:** Large tailnet simulations (thousands of nodes) reserved for separate performance testing pipelines.  
- **Visual Regression:** Static UI snapshots are brittle; instead, rely on focused API/behavior tests.  

**Manual Test Management:**  
- Document these cases in JIRA as “Manual Checks” with step-by-step checklists.  
- Assign to QA during release sprints and track completion via Xray test runs tagged `manual`.

## 6. When do you run these tests? (Scheduling & execution)

- **On Commit / PR:**  
  GitHub Actions runs unit and API tests (fast suite) on every push to `main` and every pull request.

- **Nightly Full Regression:**  
  A scheduled GitHub Actions workflow (CRON at 02:00 AM CT) runs the complete suite, including UI and E2E/network tests.

- **Release Branch Validation:**  
  Manual workflow dispatch for staging or release branches to run a targeted regression before deployment.

- **Local Developer Runs:**  
  Developers can execute `pytest -q --maxfail=1 --disable-warnings` on their machines for quick feedback.

## 7. Tailscale MVP flows

### macOS / iOS
1. **Join Network**  
   - Install app (Homebrew/App Store) → authenticate via OAuth2 → verify device appears in admin console.  
2. **Get Status & Authenticate**  
   - GET `/localapi/v0/status` → expect `BackendState` in (`Running`, `NeedsLogin`) → simulate expired token and confirm auto-refresh.  
3. **Mesh Connectivity**  
   - Establish WireGuard tunnel with a peer behind NAT → validate direct link or DERP relay fallback.  
4. **MagicDNS Resolution**  
   - Resolve `<peer>.tailscale.net` → confirm correct 100.x.x.x address.  
5. **Exit Node Routing**  
   - Enable exit node → fetch public IP matches exit node; disable → direct routing.  
6. **Subnet Routes**  
   - Advertise `192.168.1.0/24` → verify access to a resource (e.g., web server) on that subnet.  
7. **ACL Enforcement**  
   - Apply policy denying ICMP/SSH → attempt ping/`tailscale ssh` → expect failure.  
8. **Taildrop File Transfer**  
   - Send a test file → receive on peer → checksum match.  
9. **Funnel Exposure**  
   - Expose local HTTP service via Funnel → HTTP GET returns expected payload.  
10. **Telemetry & Logs**  
    - Query `/localapi/v0/metrics` and `/localapi/v0/logs` → validate JSON schema and recent entries.

### Windows
1. **Install & Login**  
   - Run MSI/EXE → complete SSO via browser → verify system tray status changes to “Connected.”  
2. **Interface & Routes**  
   - Confirm `tailscale0` interface exists → check Windows route table entries for 100.x.x.x networks.  
3. **DNS Lookup**  
   - `nslookup <peer>.tailscale.net` → resolves to WireGuard IP.  
4. **Exit Node Toggle**  
   - CLI: `tailscale up --exit-node=<peer>` → public IP check; UI: toggle in system tray.  
5. **Subnet Router**  
   - `tailscale up --advertise-routes=10.0.0.0/24` → access resource (e.g., SMB share).  
6. **ACL Policy**  
   - Set deny rule → attempt `powershell tailscale ssh` and ping → expect failure.  
7. **Taildrop CLI**  
   - `tailscale file cp` to transfer → verify file integrity.  
8. **LocalAPI Health**  
   - `tailscale status --json` & `GET http://localhost:41112/localapi/v0/status` → validate fields.  


