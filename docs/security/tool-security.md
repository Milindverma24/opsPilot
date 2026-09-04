# Tool Security & Safe Action Execution (Phase 14)

## 1. Anti-Arbitrary Execution Defense

OpsPilot strictly rejects dynamic runtime code execution tools:
- **Prohibited Tools**: `RUN_CODE`, `EXECUTE_SQL`, `EXECUTE_SHELL`, `EVAL`, `SYSTEM_CALL`, `ARBITRARY_HTTP`.
- **Enforcement Location**: Intercepted at Step 0 in `ToolExecutionService.execute()`.
- **Response**: Returns `BLOCKED` with code `ARBITRARY_EXECUTION_PROHIBITED` and writes an immutable audit record to `SecurityEvent`.

---

## 2. SSRF Protection (`SSRFProtectionService`)

All outbound network requests (e.g. document scraping, webhook calls, image indexing) pass through `SSRFProtectionService.validate_url()`:
- **Prohibited Hostnames**: `localhost`, `127.0.0.1`, `::1`, `0.0.0.0`
- **Prohibited IP Ranges**:
  - `10.0.0.0/8` (Private network)
  - `172.16.0.0/12` (Private network)
  - `192.168.0.0/16` (Private network)
  - `169.254.169.254` (Cloud Instance Metadata Service)
  - `metadata.google.internal` (Google Cloud metadata)
- **Allowed Schemes**: Only `http` and `https` (rejects `ftp`, `file`, `gopher`).

---

## 3. File Security Guardrails (`FileSecurityService`)

- **Extension Whitelist**: `.pdf`, `.csv`, `.json`, `.txt`, `.docx`, `.png`, `.jpg`
- **Prohibited Executables**: `.exe`, `.sh`, `.bat`, `.py`, `.js`, `.bin`, `.msi`
- **Size Limit**: Maximum 10MB per uploaded file
- **Path Traversal Sanitization**: Strips `../` and directory navigation characters
- **Zip Bomb Defense**: Enforces uncompressed threshold limits on archive files.
