# TeacherAssist audit remediation

Updated 2026-09-06.

All twelve findings are implemented and verified in the project test environment. The pre-change encrypted settings backup is stored outside the repository at `C:\Users\cbluemling\Python\TeacherAssist-backups\pre-audit-fix-2026-09-06`.

| Finding | Result |
| --- | --- |
| Saved state could be overwritten during startup | The client awaits bootstrap before loading `App`; read failures show a retry screen and never use an empty fallback. State replacements require an optimistic `stateRevision`. |
| OCR references were omitted from privacy routing | Chat and summary routes resolve OCR jobs before the privacy decision. Unknown references are non-public. |
| Loopback Ollama could still use cloud inference | Sensitive chat, summary, and VLM OCR requests verify the selected model through `/api/show`; cloud tags, upstream metadata, and failed probes are rejected before content is sent. |
| Historical OCR disagreements blocked corrected text | Approval and grading use the unresolved-critical predicate. An edit after approval revokes that approval. |
| PDF OCR import and bytes path were broken | The relative import is corrected and PDFium receives PDF bytes directly. |
| Fresh chat had no active ID | Chat initialization is normalized once and always creates a UUID active chat. |
| Capability polling reset settings | Settings are initialized once from bootstrap, saved serially after edits, and the 30-second endpoint only refreshes capability and credential status. |
| Protected export links used browser navigation | UI exports and markdown export links use authenticated `fetch`, a temporary blob URL, and URL revocation. |
| Bootstrap invalidated other tabs | Bootstrap reuses an active session and CSRF token. The client refreshes authentication once only after `AUTH_REQUIRED`. |
| Deleted OCR work could reappear | Durable deletion markers, tracked futures, and lifecycle locking prevent queued/running work and image rendering from recreating a deleted job. |
| Legacy synchronous OCR timeout waited | The bounded slot returns 504 immediately on timeout and remains occupied until its worker exits; concurrent requests receive 503. |
| Delete-after-approval did nothing | Approval honors `ocrDeleteAfterApproval`, removes originals and generated scan images, retains approved text and records, and retries marked cleanup at startup. |

Verification completed:

- `tools\.venv\Scripts\python.exe -m pytest -q` with an isolated runtime directory: **420 passed, 1 skipped**.
- Targeted regression coverage covers state revisions, model locality, PDF byte loading, timeout slot behavior, OCR approval/cleanup/deletion races, and session reuse.
- `npm run build` completed successfully and regenerated `web_dist` and `service-worker.js`.
- `npm run test:browser` against locally installed Microsoft Edge: **4 passed**. It covers bootstrap hydration without a replacement write, revisioned saving after an edit, the retry screen on persistence failure, and authenticated downloads from both export UI paths.
