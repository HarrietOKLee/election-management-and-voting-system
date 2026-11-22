# 11. Requirements traceability matrix

This matrix links every requirement to the place where it is designed and implemented and to
the test cases that check it (requirement → design → implementation → testing). It is generated
from the tables in documents 00 to 10 and 14; when a module document changes, update this file too.

How to read it:

- "Design and code" is the module, route or error code that implements the requirement. The
  use case and sequence diagram of the requirement are in the module document named in the
  heading.
- "Manual test cases" are system tests run by hand on the demo server; their steps, expected
  results and recorded results are in the module document.
- "Automated tests" are files of the pytest suite as it existed at commit `c68fb54`; the exact
  test function for each requirement is listed in the module document. The mapping was made
  by reading the project history, in some cases from the test name alone, and must be
  confirmed when the suite is restored (document 12).
- "—" means no test case is listed yet. These gaps are collected in section 3.

## 1. Functional requirements

### 00 Overview (person in charge: group)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-SYS-01 | Reject every request that does not carry a valid session, except sign-in and the health check. | `server/app.py` (401 `session_expired`) | — | — |
| FR-SYS-02 | Allow an operational user to read and write only the stations assigned to that user. | `server/station_access.py` (403 `station_access_denied`) | — | — |
| FR-SYS-03 | Accept writes only for the single active election, and make a finalised election read-only. | `server/station_access.py`, `server/lifecycle.py` (409 `active_election_required`) | TC-FIN-03 | — |
| FR-SYS-04 | Keep every saved revision of a record. A correction creates a new revision and require a reason. | `*_models.py` revision tables | TC-BOX-07, TC-SPP-04, TC-ACC-02 | — |
| FR-SYS-05 | Require the Supervisor to re-enter their own password when approving a record, and approve only the … | `verify_password` calls in `polling.py`, `turnout.py`, `accounting.py`, `counting_workflow.py` and others | TC-CNT-09 | — |
| FR-SYS-06 | Produce a statement of a saved record as an on-screen preview, a CSV file and a PDF file in the language … | `server/*_reports.py`, `desktop/report_files.py` | TC-BOX-08, TC-SPP-06, TC-ACC-03, TC-CNT-12, TC-FIN-04 | — |
| FR-SYS-07 | Record an audit event (actor, action, time) for sign-in, sign-out, password change and every write. | `audit_events` table | — | — |

### 01 Login and layout (person in charge: Rico)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-AUTH-01 | Authenticate a user by username and password and issue a session token. | `POST /api/auth/login` | TC-AUTH-01 | — |
| FR-AUTH-02 | Return the same error for a wrong password and for an unknown username. | `invalid_credentials` in `app.py` | TC-AUTH-02 | `test_auth_api.py` |
| FR-AUTH-03 | Force a user who signs in with a temporary password to change it before any workspace function is … | 403 `password_change_required`; `GET /api/workspace` | TC-AUTH-03 | `test_auth_api.py` |
| FR-AUTH-04 | Accept a new password only if it has 12 to 128 characters, differs from the current password, and the … | `POST /api/auth/password` | TC-AUTH-04 | — |
| FR-AUTH-05 | Revoke all other sessions of the account when its password changes. | `app.py` | — | `test_auth_api.py` |
| FR-AUTH-06 | End a session on sign-out and 24 hours after sign-in. There shall be no inactivity time-out. | `DELETE /api/auth/session`; session expiry | — | `test_auth_api.py` |
| FR-AUTH-07 | Let the administrator create a staff account with display name, role, enabled flag and assigned … | `POST /api/accounts`, `PUT /api/accounts/{id}`, `POST /api/accounts/{id}/password-reset` | TC-AUTH-03 | — |
| FR-AUTH-08 | Refuse sign-in for a disabled account and revoke existing sessions when a role or station assignment … | `staff.py` | — | `test_staff_api.py` |
| FR-AUTH-09 | Always keep at least one enabled administrator. | `staff.py` (last administrator check) | — | `test_staff_api.py` |
| FR-AUTH-10 | Show each user only the stations assigned to them and the navigation items permitted for their role. | `GET /api/workspace/stations`; `Main.qml` | TC-AUTH-01 | — |
| FR-AUTH-11 | Let the user switch the interface language between Traditional Chinese, Simplified Chinese and English … | `DesktopController.setLocale` | TC-AUTH-05 | — |
| FR-AUTH-12 | Let the administrator read the audit history of an account without exposing passwords, hashes or tokens. | `GET /api/accounts/{id}/audit` | — | `test_staff_api.py` |

### 02 Polling times (person in charge: Dennis)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-POL-01 | Record four polling events per station: actual opening, closure to new arrivals, queue-clear estimate … | `PollingKind` in `polling.py`; `PUT /{kind}` | TC-POL-01 | — |
| FR-POL-02 | Compare the actual opening time with the planned opening time in the election schedule and show the … | `record_view` (`opening_status`) | — | `test_polling_api.py` |
| FR-POL-03 | Require a delay reason before a delayed opening can be submitted. | `validate_record` | — | `test_polling_api.py` |
| FR-POL-04 | Reject an event time in the future and any set of times that is out of order (opening ≤ closure ≤ … | `validate_record` (422 `polling_validation`) | TC-POL-04 | `test_polling_api.py` |
| FR-POL-05 | Let the polling officer save a draft and then submit one revision for approval. | `POST /{kind}/submit` | TC-POL-02 | — |
| FR-POL-06 | Let only a Supervisor approve a submitted revision, after re-entering the Supervisor's own password. | `POST /{kind}/approve` (403 role check, 401 `invalid_credentials`) | TC-POL-03, TC-POL-06 | `test_polling_api.py` |
| FR-POL-07 | Let the polling officer amend a submitted or approved event only with an amendment reason; the amended … | `POST /{kind}/amend` | TC-POL-05 | `test_polling_api.py` |
| FR-POL-08 | Show the revision and approval history of each event, including who entered, submitted and approved it … | `GET /{kind}/history`, `GET /audit` | TC-POL-01 | — |
| FR-POL-09 | Refuse polling entries until the administrator has saved the election schedule. | 409 `schedule_not_configured` | — | — |

### 03 Stock and allocations (person in charge: Harriet)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-STK-01 | Record a stock receipt with ballot series, receipt time and one or more inclusive serial ranges, each … | `POST /stock` (`StockInput`) | TC-STK-01 | `test_stock_api.py` |
| FR-STK-02 | Reject a receipt whose declared pool quantities do not equal the quantities implied by its serial ranges. | `StockInput.conserved_pools` | — | `test_stock_api.py` |
| FR-STK-03 | Reject a serial range that overlaps any range already received in the same series and constituency. | 409 `stock_overlap` | TC-STK-06 | `test_stock_api.py` |
| FR-STK-04 | Treat serial numbers as digit strings of up to 18 digits and keep leading zeros exactly as printed. | `stock_serials.py` | — | `test_stock_api.py` |
| FR-STK-05 | Record an allocation of one ordinary serial range to one issuing desk with the hand-over time. | `POST /allocations` (`AllocationInput`) | TC-STK-02 | — |
| FR-STK-06 | Reject an allocation that is outside received ordinary stock or that overlaps a range currently owned by … | 409 `allocation_overlap` | TC-STK-03, TC-STK-04 | `test_allocation_api.py` |
| FR-STK-07 | Show, for the station, the ordinary stock still held centrally and the ranges currently owned by each … | `GET /allocations`, `stock_inventory.py` | TC-STK-01 | — |
| FR-STK-08 | Record the return of unissued papers from a desk to the presiding officer, after which the range may be … | `POST /stock-returns` (409 `return_outside_owned_stock`) | — | — |
| FR-STK-09 | Allow a correction of a receipt, allocation or return only with a reason, and keep every earlier … | `PUT /{id}`; `GET /{id}/history` | TC-STK-05 | `test_allocation_api.py` |
| FR-STK-10 | Refuse a correction that would remove papers already owned by a desk or already observed as issued. | `preserve_allocations` in `stock_inventory.py` | — | `test_allocation_api.py` |
| FR-STK-11 | Export the received-stock statement and the allocation statement as CSV and PDF. | `stock_reports.py`, `allocation_reports.py` | TC-STK-07 | — |

### 04 Snapshots and turnout (person in charge: Toby)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-SNP-01 | Record a snapshot with an observation time and, for each issuing desk, the serial ranges of papers … | `POST /stock-snapshots` (`StockSnapshotInput`) | TC-SNP-01 | `test_stock_snapshot_api.py` |
| FR-SNP-02 | Calculate the ordinary papers issued by each desk and by the station as papers owned by the desk at the … | `stock_snapshots.py` | TC-SNP-01 | `test_stock_snapshot_api.py` |
| FR-SNP-03 | Reject a remaining range that the desk does not own, and any snapshot that would make issued papers … | 409 `remaining_outside_owned_stock`, `negative_issuance` | TC-SNP-02, TC-SNP-03 | `test_stock_snapshot_api.py` |
| FR-SNP-04 | Distinguish a desk that was not reported from a desk reported with zero papers remaining. | `stock_snapshots.py` | — | `test_stock_snapshot_api.py` |
| FR-SNP-05 | Reject a snapshot time in the future. | 422 `event_time_in_future` | — | — |
| FR-SNP-06 | Allow a snapshot to be corrected only with a reason, keeping the earlier revision. | `PUT /stock-snapshots/{id}` | TC-SNP-04 | — |
| FR-SNP-07 | Mark a snapshot as needing review when an allocation it depends on is changed afterwards. | snapshot basis check | — | `test_stock_snapshot_api.py` |
| FR-TUR-01 | Divide polling hours into reporting periods from the planned opening time using the reporting interval … | `reporting_periods.py`, `ScheduleInput.reporting_interval_minutes` | — | `test_turnout_api.py` |
| FR-TUR-02 | Accept, for a period, the turnout of the period, the cumulative turnout, or both, and derive the missing … | `PUT /turnout/{period}` (`supplied_hourly`, `supplied_cumulative`) | — | `test_turnout_api.py` |
| FR-TUR-03 | Reject figures that are inconsistent: a cumulative total lower than the previous period, or period and … | 422 `turnout_validation` | — | `test_turnout_api.py` |
| FR-TUR-04 | Treat a missing period and a period reported as zero as different states. | `turnout.py` | — | `test_turnout_api.py` |
| FR-TUR-05 | Allow a period to be submitted only after the period has ended, and only with the time the figure was … | `POST /turnout/{period}/submit`; `validate_content` | — | `test_turnout_api.py` |
| FR-TUR-06 | Let only a Supervisor approve a submitted period, after re-entering the Supervisor's own password. | `POST /turnout/{period}/approve` | TC-TUR-03, TC-TUR-04 | `test_turnout_api.py` |
| FR-TUR-07 | Allow an amendment of a submitted or approved period only with a reason, and then require every later … | `POST /turnout/{period}/amend`; 409 `turnout_review_required` | TC-TUR-02 | `test_turnout_api.py` |
| FR-TUR-08 | Show the cumulative turnout over the continuous run of approved periods from the opening. | `GET /turnout` | TC-TUR-01 | — |
| FR-TUR-09 | Record how each figure was obtained: copied from the external register (normal), calculated from … | `mode` = `normal` / `fallback` / `recovery`; see document 06 | — | — |
| FR-TUR-10 | Export the station turnout statement and a single-period statement as CSV and PDF. | `turnout_reports.py` | TC-TUR-05 | — |

### 05 Complaints and queue (person in charge: John)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-CMP-01 | Record a complaint case with a unique case reference, received time, category, description and work … | `POST /complaints` (`ComplaintInput`) | TC-CMP-01, TC-CMP-02 | `test_complaints_api.py` |
| FR-CMP-02 | Provide a default list of complaint categories for each election and let the administrator add, rename … | `complaint_categories.py` (`DEFAULT_CATEGORIES`) | TC-CMP-05 | `test_complaints_api.py` |
| FR-CMP-03 | Let the officer mark a case as completed with a completion time, and amend a case only with a reason … | `PUT /complaints/{id}`, `POST /complaints/{id}/amend`, `GET /complaints/{id}/history` | TC-CMP-03 | `test_complaints_api.py` |
| FR-CMP-04 | Keep the category name a case was recorded under, even if the category is later renamed or disabled. | `complaint_models.py` (pinned labels) | — | `test_complaints_api.py` |
| FR-CMP-05 | Assign each case to a reporting period by its received time and count the cases of each period by … | `complaint_periods.py`, `reporting_periods.py` | — | — |
| FR-CMP-06 | Allow a period to be prepared, submitted after the period has ended, and approved by a Supervisor with … | `PUT /complaint-periods/{period}`, `/submit`, `/approve` | TC-CMP-04 | `test_complaint_periods_api.py` |
| FR-CMP-07 | Mark an approved period as needing renewal when a case is recorded later with a received time inside … | `complaint_periods.py` | — | `test_complaint_periods_api.py` |
| FR-CMP-08 | Export complaint statistics for the station and for one period as CSV and PDF. | `complaint_reports.py` | — | — |
| FR-QUE-01 | Record a queue observation with observation time and one of four waiting-time bands: under 30 minutes … | `POST /queue` (`QueueBand`) | TC-QUE-01 | `test_queue_api.py` |
| FR-QUE-02 | Let the officer confirm that the band is unchanged, and store the confirmation as its own history entry. | `POST /queue/confirm` | TC-QUE-02 | `test_queue_api.py` |
| FR-QUE-03 | Show when the next update is due (30 minutes after the latest observation or confirmation) and how many … | `queue_freshness` in `queue.py` | TC-QUE-01 | `test_queue_api.py` |
| FR-QUE-04 | Keep the history of all observations and confirmations and not let a back-dated entry replace the latest … | `queue_models.py` | TC-QUE-02 | `test_queue_api.py` |
| FR-QUE-05 | Export the queue history as CSV and PDF. | `queue_reports.py` | — | — |

### 06 Failure handling (person in charge: Mody)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-FBK-01 | Record a fallback activation with the original event time, the cumulative turnout supplied at that … | `POST /fallback` (`FallbackDraft`, `kind = activation`) | TC-FBK-01 | `test_fallback_activation_api.py` |
| FR-FBK-02 | Refuse an activation whose snapshot is at a different time, is not current, or does not report every … | 409 `fallback_balance_time_required`, 409 `fallback_review_required` (`turnout_basis.py`) | TC-FBK-02 | `test_fallback_integrity_api.py` |
| FR-FBK-03 | Require Supervisor confirmation with password before an activation or recovery takes effect. | `POST /fallback/{id}/approve` | TC-FBK-01, TC-FBK-03 | `test_fallback_activation_api.py` |
| FR-FBK-04 | Calculate the turnout of a period as the activation figure plus ordinary papers issued since the … | `turnout.py` (`mode = fallback`; "Fallback turnout is calculated from ordinary stock") | — | `test_fallback_turnout_api.py` |
| FR-FBK-05 | Exclude replacement and tendered papers from the calculated turnout. | `turnout_basis.py` | — | `test_fallback_turnout_api.py` |
| FR-FBK-06 | Record a recovery that refers to its confirmed activation and holds the recovered external figure, and … | `kind = recovery`; "Recovery comparison" | — | `test_fallback_recovery_api.py` |
| FR-FBK-07 | Keep the earlier stock-based turnout revision when a period is renewed with the recovered figure. | `turnout.py` (`mode = recovery`) | — | `test_fallback_recovery_api.py` |
| FR-FBK-08 | Reject a new activation that overlaps a confirmed fallback interval. | `fallback_source_conflict` | — | `test_fallback_mode_conflicts_api.py` |
| FR-FBK-09 | Allow a correction of a confirmed activation or recovery only with a reason, and require renewed … | `POST /fallback/{id}/amend` | — | — |
| FR-OUT-01 | Record an outage with reference, type (network, backend, database, unknown), actual start and end time … | `POST /outages` (`OutageDraft`) | TC-OUT-01, TC-OUT-02 | — |
| FR-OUT-02 | Register each paper record made during the outage with its paper reference, the time written on the … | `POST /outages/{id}/paper-records` | TC-OUT-03 | — |
| FR-OUT-03 | Re-enter a paper record through the normal workflow exactly once and attach an immutable receipt to the … | `paper_reentry.py` | — | `test_outage_reconciliation_api.py` |
| FR-OUT-04 | Let an officer link a paper reference to an entry that already reached the server before the outage was … | `POST /outages/{id}/paper-records/{paper_id}/link-receipt` | — | `test_outage_allocation_reentry_api.py` |
| FR-OUT-05 | Let a Supervisor approve the reconciliation of an outage only when every paper reference has been … | `POST /outages/{id}/approve` | TC-OUT-03 | `test_outage_reconciliation_api.py` |
| FR-OUT-06 | Export the outage and paper reconciliation report as CSV and PDF. | `outage_reports.py` | — | — |
| FR-REC-01 | The client shall keep a local journal of operational requests whose outcome is pending or uncertain. The … | `client_command_journal.py` (`SENSITIVE_KEYS`) | — | `test_client_recovery_desktop.py` |
| FR-REC-02 | Let the user check the server outcome of a journalled request by its request identifier. | `GET /request-outcomes/{request_id}` | TC-REC-02 | `test_client_recovery_desktop.py` |
| FR-REC-03 | The client shall allow a retry of the original request only after the server has answered that no … | `recovery.py` (`checkOutcome`, `retry`) | — | `test_client_recovery_contract_desktop.py` |
| FR-REC-04 | The server shall answer 503 `database_unavailable` when the database cannot be reached and not leave a … | `app.py` | TC-REC-01 | `test_auth_api.py` |

### 07 Post-poll times (person in charge: Lam)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-BOX-01 | Record a ballot box with box reference, seal reference and preparation time. The box reference shall be … | `POST /boxes` (`BoxCreate`; 409 `box_reference_exists`) | TC-BOX-01, TC-BOX-02 | `test_box_api.py` |
| FR-BOX-02 | Set the receiving counting station of a box from the station configuration: the same station when it … | `station_models.py` (`counting_mode` = `local` / `send`) | — | `test_box_api.py` |
| FR-BOX-03 | Record the departure time of a box at the origin station. | `POST /boxes/{id}/departure` | — | `test_box_api.py` |
| FR-BOX-04 | Record the receipt time of a box at the receiving station. A transferred box shall require a recorded … | `POST /boxes/{id}/receipt` (409 `box_departure_required`) | TC-BOX-04, TC-BOX-05 | `test_box_api.py` |
| FR-BOX-05 | Reject a time in the future and a receipt time earlier than the departure time. | 422 `box_validation` | TC-BOX-03 | — |
| FR-BOX-06 | Record three counting milestones at a counting station: conversion complete, first box opening (naming … | `PUT /boxes/milestones/{kind}` (`MILESTONE_KINDS`) | TC-BOX-06 | `test_box_api.py` |
| FR-BOX-07 | Keep the milestones in chronological order and not accept a first box opening earlier than the receipt … | `save_milestone` (409 `box_receipt_required`, 422 `box_validation`) | TC-BOX-06 | — |
| FR-BOX-08 | Require a reason for every correction of a departure, receipt or milestone and keep the earlier entry. | `PUT /boxes/{id}/departure`, `PUT /boxes/{id}/receipt` (422 `box_correction_reason_required`) | TC-BOX-07 | `test_box_api.py` |
| FR-BOX-09 | Show the count completion time from the submitted count round and show "not recorded" until then. | `counting_round_events.py`, `box_state.py` | TC-CNT-08 | `test_box_api.py` |
| FR-BOX-10 | Export the box handover and counting timeline report as CSV and PDF. | `box_reports.py` | TC-BOX-08 | — |

### 08 Special papers (person in charge: Salina)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-SPP-01 | Record a special-paper observation with observation time and, for each ballot series received, six … | `POST /special-papers` (`SpecialPaperInput`) | — | `test_special_papers_api.py` |
| FR-SPP-02 | Base each observation on one current and complete P(12) snapshot and take the ordinary papers issued … | `stock_snapshot_id`, `stock_snapshot_revision`; 409 `stock_snapshot_basis_stale`, `stock_snapshot_incomplete` | — | — |
| FR-SPP-03 | Calculate, for each series and for the station: total retrieved-unused papers, unissued ordinary papers … | `special_papers.py` (`QUANTITIES`) | TC-SPP-01 | `test_special_papers_api.py` |
| FR-SPP-04 | Reject an observation in which replacement papers issued differ from spoilt originals surrendered. | 409 `replacement_spoilt_mismatch` | TC-SPP-02 | — |
| FR-SPP-05 | Reject quantities that exceed their source: replacement or tendered papers issued above the reserve … | 409 `special_paper_bounds` | TC-SPP-03 | — |
| FR-SPP-06 | Require every received series to be reported exactly once. | 409 `special_paper_series_incomplete` | — | — |
| FR-SPP-07 | Reject a later observation that reports fewer replacement or tendered papers issued than an earlier one. | 409 `special_paper_issuance_regression` | — | `test_accounting_freshness_api.py` |
| FR-SPP-08 | Treat "no observation saved" and "observation saved with zero" as different states. | `special_papers.py`; "Set all counts to zero" | TC-SPP-01 | — |
| FR-SPP-09 | Allow a correction only with a reason and keep the earlier revision. | `PUT /special-papers/{id}` (`SpecialPaperCorrection`) | TC-SPP-04 | `test_accounting_edges_api.py` |
| FR-SPP-10 | Not change turnout or ordinary stock when special papers are recorded. | `special_papers.py` | TC-SPP-05 | `test_special_papers_api.py` |
| FR-SPP-11 | Export the selected special-paper statement as CSV and PDF. | `special_paper_reports.py` | TC-SPP-06 | — |

### 09 Count reports (person in charge: Toby)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-ACC-01 | Prepare the ballot paper account of a station from one special-paper observation revision and … | `PUT /accounting` (`AccountingInput`) | — | `test_accounting_api.py` |
| FR-ACC-02 | Calculate all account quantities and reject an account that does not balance. | `accounting.py` (409 `accounting_balance_invalid`) | TC-ACC-01 | `test_accounting_api.py` |
| FR-ACC-03 | Give two estimates of the papers in the boxes: from stock, and from turnout only when the turnout record … | `estimated_box_from_stock_quantity`, `estimated_box_from_turnout_quantity` | TC-ACC-01 | — |
| FR-ACC-04 | Reject a turnout period that ends after the special-paper observation. | 409 `accounting_turnout_time_invalid` | — | — |
| FR-ACC-05 | Follow the reviewed-record workflow: draft, submit, approve by a Supervisor with password; a correction … | `POST /accounting/submit`, `/approve` (422 `accounting_reason_required`) | TC-ACC-02 | `test_accounting_api.py` |
| FR-ACC-06 | Mark an account as needing review when one of its sources is changed afterwards. | `accounting_source_stale`; "Sources changed" | — | `test_accounting_edges_api.py` |
| FR-ACC-07 | Export the account as CSV and PDF. | `accounting_reports.py` | TC-ACC-03 | — |
| FR-CNT-01 | Define a counting scope at a counting station: a reference, the received boxes to be counted together … | `POST /counting-scopes` | TC-CNT-01 | — |
| FR-CNT-02 | Not allow a box to belong to two scopes. | 409 `box_already_in_scope` | — | `test_counting_scope_edges_api.py` |
| FR-CNT-03 | Allow count entry only when every box in the scope is received and every source account is approved. | blockers `box_receipt_missing`, `source_accounting_missing`, `source_accounting_unapproved`; 409 `count_scope_not_ready` | TC-CNT-01 | `test_counting_scopes_api.py` |
| FR-CNT-04 | Record F1 for a scope: observation time, valid votes per candidate, clearly invalid papers per reason … | `POST/PUT /rounds` (`counting_rounds.py`) | TC-CNT-02 | `test_counting_rounds_api.py` |
| FR-CNT-05 | Accept only whole numbers of zero or more, and treat a blank quantity as "not observed", not as zero. | `counting_round_models.py`; blockers `f1_candidate_missing` etc. | TC-CNT-04 | `test_counting_rounds_api.py` |
| FR-CNT-06 | Take the invalid-paper reasons from the catalogue maintained by the Administrator (defaults: seven … | `invalid_ballot_reasons.py`; 422 `invalid_reason_explanation_required` | TC-CNT-07 | `test_counting_rounds_api.py` |
| FR-CNT-07 | Reject an F1 in which all quantities are entered but actual papers counted differ from candidate votes … | 422 `f1_arithmetic_invalid` | TC-CNT-03 | `test_counting_rounds_api.py` |
| FR-CNT-08 | Record F2: start time of determination, questionable papers accepted per candidate and rejected per … | `PUT /rounds/{id}/f2` (`counting_outcomes.py`) | TC-CNT-06 | `test_counting_outcomes_api.py` |
| FR-CNT-09 | Reject an F2 whose outcomes exceed the questionable papers of F1, and an F2 in which all outcomes are … | 422 `f2_outcomes_exceed_questionable`, `f2_outcomes_unbalanced` | TC-CNT-05a | `test_counting_outcomes_api.py` |
| FR-CNT-10 | Calculate F3 and F4 from F1 and F2 without further input. | `counting_totals.py` | TC-CNT-02, TC-CNT-06 | `test_counting_outcomes_api.py` |
| FR-CNT-11 | Compare actual papers counted with the stock estimate and the turnout estimate of the scope and show … | `counting_totals.py` (`f2_physical_comparisons`) | TC-CNT-13 | — |
| FR-CNT-12 | Accept submission of a count only when all observations are present and balanced, and record the count … | `POST /rounds/{id}/submit` (409 `count_inputs_incomplete`) | TC-CNT-05, TC-CNT-08 | `test_counting_workflow_api.py` |
| FR-CNT-13 | Require a Supervisor to accept every known physical difference with a reason before approval. | `POST /rounds/{id}/physical-differences/{source}/accept`; 409 `count_physical_difference_unaccepted` | TC-CNT-13 | — |
| FR-CNT-14 | Require the Supervisor's own password to approve one exact revision of a count. | `POST /rounds/{id}/approve` | TC-CNT-09, TC-CNT-10 | `test_counting_workflow_api.py` |
| FR-CNT-15 | Require the Supervisor's own password to select an approved round as the current result of the scope … | `POST /rounds/{id}/select` | TC-CNT-11 | `test_counting_workflow_api.py` |
| FR-CNT-16 | Require a reason to correct a submitted F1 or F2 and keep the submitted revision; a corrected revision … | `POST /rounds/{id}/amend-f1`, `/amend-f2` (422 `count_amendment_reason_required`) | — | — |
| FR-CNT-17 | Preview and export F1, F2, F3, F4 and the complete count record as CSV and PDF in the selected language. | `f1_reports.py`, `count_reports.py` | TC-CNT-12 | `test_count_reports_api.py` |

### 10 Recount and completion (person in charge: Lam)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-RCT-01 | Let a Supervisor instruct a recount of one counting scope, giving instruction time, reason and the … | `POST /counting-scopes/{scope_id}/recounts` (`local_recounts.py`) | TC-RCT-01, TC-RCT-02 | `test_local_recounts_api.py` |
| FR-RCT-02 | Allow a recount instruction only for a scope whose current approved round is selected, and refuse a … | 409 `count_scope_not_ready`, `local_recount_pending` | TC-RCT-03 | — |
| FR-RCT-03 | On a recount instruction the system shall create a new round with all quantities blank on the same scope … | `local_recounts.py` (`instruction_only` blank round) | TC-RCT-02, TC-RCT-04 | `test_local_recounts_api.py` |
| FR-RCT-04 | Keep the earlier selected round as the result of the scope until the new round has been submitted … | `recount_state.py`; "Previous approved selection retained; recount pending" | TC-RCT-02 | `test_local_recounts_api.py` |
| FR-RCT-05 | After a recount instruction the system shall allow only the new round to be selected. | 409 `local_recount_required_round` | TC-RCT-04 | — |
| FR-RCT-06 | Let a Supervisor instruct a recount of a whole constituency in one action that creates a blank round in … | `POST /constituencies/{id}/recounts` (`constituency_recounts.py`) | — | `test_constituency_recounts_api.py`, `test_election_completion_api.py` |
| FR-RCT-07 | Refuse a constituency recount when the result has changed since the Supervisor loaded it. | `basis_digest`; 409 `constituency_result_basis_stale`, `constituency_recount_sources_stale` | — | — |
| FR-RCT-08 | Show, for each recount instruction, the progress of each new round: incomplete, submitted, approved … | `constituency_recount_state.py` | — | `test_constituency_recount_progress_api.py` |
| FR-RES-01 | Calculate the valid votes of each candidate in a constituency as the sum of the selected, approved … | `GET /constituencies/{id}/results` (`constituency_results.py`) | TC-RES-01, TC-RES-03 | `test_constituency_results_api.py` |
| FR-RES-02 | List every pending item (scope not ready, no selected count, selected count out of date, box not in a … | `pending` list in `constituency_results.py` | — | `test_constituency_results_api.py` |
| FR-RES-03 | Not include a count that is only submitted or only approved in the candidate totals. | `constituency_results.py` | — | `test_constituency_results_api.py` |
| FR-RES-04 | Show the tie and let the Supervisor record which tied candidate is returned, with reason and password. | `POST /results/tie-resolutions` (422 `tie_candidate_invalid`, `tie_resolution_reason_required`) | — | `test_constituency_tie_api.py`, `test_election_completion_api.py` |
| FR-RES-05 | Show the result as provisional until the election is finalised. | "Provisional result" / "Finalized result" | TC-RES-01 | — |
| FR-RES-06 | Export the constituency result report as CSV and PDF. | `constituency_reports.py` | — | `test_constituency_result_reports_api.py` |
| FR-FIN-01 | Show whether the election can be finalised and list every blocker: service completion of a station … | `GET /elections/{id}/completion` (`_assess_completion`) | TC-FIN-01 | `test_election_completion_api.py` |
| FR-FIN-02 | Let only a Supervisor assigned to every station of the election finalise it, with the Supervisor's own … | `POST /finalizations` (403 `full_election_access_required`, 409 `election_not_ready`) | TC-FIN-02 | `test_election_completion_api.py` |
| FR-FIN-03 | Refuse finalisation when the facts have changed since the Supervisor reviewed them. | `basis_digest`; 409 `election_completion_basis_conflict` | — | — |
| FR-FIN-04 | On finalisation the system shall store the outcome and make all operational records of the election … | `lifecycle.py`; FR-SYS-03 | TC-FIN-03 | — |
| FR-FIN-05 | Let a Supervisor reopen a finalised election with a reason and password; the earlier finalisation stays … | `POST /reopenings` (409 `finalized_election_required`) | TC-FIN-05 | — |
| FR-FIN-06 | Keep a history of finalisations and reopenings and export the statement of each as CSV and PDF. | `GET /completion/history`, `election_completion_reports.py` | TC-FIN-04 | — |

### 14 E-polling (person in charge: Dennis)

| Requirement | Summary | Design and code | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- |
| FR-EPL-01 | Let the Administrator choose the voting method of an election (physical ballots or e-polling) while the … | `configuration.py` (`voting_method`, 409 `draft_required`); migration `0036_electronic_voting` (`server_default="paper"`); `qml/ConfigurationSection.qml` | TC-EPL-09 | — |
| FR-EPL-02 | Allow an e-polling election to be activated without issuing desks. A physical-ballot election shall … | `lifecycle.py` `complete_configuration` | — | — |
| FR-EPL-03 | In an e-polling election the system shall reject writes to paper-only records (stock receipts … | `station_access.py` 409 `paper_election_required`, called from `stock_scope`, `turnout_scope` and the box router; `Main.qml` `electronicElection` | TC-EPL-08 | — |
| FR-EPL-04 | Start a voting session only for a Polling Officer assigned to the station, only in an active e-polling … | `epolling.py` `start`; 403 `polling_officer_required`, 409 `epolling_not_enabled`, 409 `epolling_service_closed` | TC-EPL-01, TC-EPL-13 | — |
| FR-EPL-05 | On starting a session the system shall return the candidates of the station's constituency in … | `current_candidates`; 409 `epolling_no_candidates` | TC-EPL-01 | — |
| FR-EPL-06 | Record exactly one electronic vote for one candidate of the constituency when the elector casts the … | `PUT /sessions/vote`; 422 `epolling_candidate_unavailable` | TC-EPL-02 | — |
| FR-EPL-07 | Count a session at most once. Repeating the cast request of a recorded session, or the start request of … | `cast` and `start` return `{"status": ...}`; row lock on the session | TC-EPL-10 | — |
| FR-EPL-08 | Refuse a vote when the candidate list has changed since the session started, so that the elector never … | `candidate_list_digest`; 409 `epolling_candidates_changed` | — | — |
| FR-EPL-09 | Allow a session to be ended without a vote. A cancelled session shall not accept a vote. Cancelling an … | `POST /sessions/cancel`; 409 `epolling_session_cancelled` | TC-EPL-05 | — |
| FR-EPL-10 | Store an electronic vote with election, constituency, station and candidate only, under its own random … | `epolling_models.py` `ElectronicVote` | TC-EPL-14 | — |
| FR-EPL-11 | The voting screen shall take the elector through three steps: choose one candidate, review the choice … | `qml/EPollingPage.qml`; `Main.qml` `voterMode` | TC-EPL-01, TC-EPL-02, TC-EPL-04 | — |
| FR-EPL-12 | After a vote is recorded the terminal shall wait for the Polling Officer, who shall be able to start the … | `epolling.py` `done`, `startNext`, `exit` | TC-EPL-03 | — |
| FR-EPL-13 | Before sending a session to the server the terminal shall save only the session reference (server … | `epolling_recovery.py` `VotingSessionJournal`; `epolling.py` `checkStatus`, `retryCast` | TC-EPL-10, TC-EPL-11 | — |
| FR-EPL-14 | Allow only one voting screen for each client state directory, and tell the user when another window is … | `QLockFile` in `epolling_recovery.py`; `epolling_screen_busy` | TC-EPL-12 | — |
| FR-EPL-15 | Show a Supervisor assigned to the station the number of electronic votes for each candidate and the … | `GET /results`; 403 `supervisor_required`; `epolling_results.py`; `qml/EPollingResultsPage.qml` | TC-EPL-06, TC-EPL-07 | — |
| FR-EPL-16 | Let a Polling Officer assigned to the station ask for the status (pending, recorded, cancelled) of a … | `POST /sessions/status`; 404 `epolling_session_not_found` | — | — |

## 2. Non-functional requirements

| Requirement | Type | Summary | Measure / how verified | Manual test cases | Automated tests |
| --- | --- | --- | --- | --- | --- |
| NFR-SEC-01 | Security | All traffic between client and server shall use HTTPS, and the client shall verify the server … | Client started with a wrong `--ca` file cannot sign in | — | `test_dev_tls.py` |
| NFR-SEC-02 | Security | Passwords shall be stored only as Argon2 hashes and session tokens only as SHA-256 digests. No … | Inspection of `accounts` and `sessions` tables; API tests | — | `test_staff_api.py`, `test_turnout_api.py` |
| NFR-SEC-03 | Security | A session shall expire exactly 24 hours after sign-in and be revoked by sign-out, by a … | API test with a controlled clock | — | `test_auth_api.py` |
| NFR-SEC-04 | Security | Role and station checks shall be enforced on the server for every route, not only in the user … | Direct API call with the wrong role returns 403 | TC-POL-06, TC-TUR-04, TC-QUE-03, TC-BOX-05, TC-CNT-10, TC-RES-02, TC-EPL-07 | `test_polling_api.py`, `test_queue_api.py` |
| NFR-REL-01 | Reliability | When two clients edit the same record revision, exactly one shall succeed; the other shall … | Concurrency API tests | — | `test_polling_api.py` |
| NFR-REL-02 | Reliability | Repeating a command with the same request identifier shall have exactly one effect. The same … | Replay API tests | TC-EPL-10 | `test_polling_api.py`, `test_allocation_api.py`, `test_complaints_api.py` |
| NFR-REL-03 | Reliability | Saved records shall survive a restart of the server and the client. | Restart tests; demo restart | — | `test_polling_api.py`, `test_stock_api.py`, `test_auth_api.py` |
| NFR-REL-04 | Reliability | If the database is unavailable the server shall answer 503 `database_unavailable` without a … | Fault-injection test; Recovery page | TC-REC-01 | — |
| NFR-USA-01 | Usability | Every screen and statement shall be available in Traditional Chinese, Simplified Chinese and … | about 1,800 translation keys in each language; inspection | — | — |
| NFR-USA-02 | Usability | All times shall be shown in Hong Kong Time and stored in UTC. | Inspection of statements | — | — |
| NFR-USA-03 | Usability | A trained officer shall be able to record one routine entry (for example a queue observation) … | `TODO(group)`: time three members on the demo | — | — |
| NFR-PERF-01 | Performance | 95% of API requests on the demo data set shall complete within 1 second on a local network. | `TODO(group)`: measure on the demo; target only | — | — |
| NFR-PORT-01 | Portability | The client shall run on Windows 11 x64 and macOS (Apple silicon and Intel). The server shall … | GitHub Actions build `build-desktop.yml` | — | — |
| NFR-DATA-01 | Accuracy | Ballot serial numbers shall be handled as exact digit strings of up to 18 digits and … | Boundary tests with leading zeros and large numbers | — | `test_stock_api.py` |
| NFR-MNT-01 | Maintainability | All code shall pass `ruff` and `mypy --strict`. The database schema shall change only through … | `pyproject.toml`; 36 migrations | — | — |
| NFR-BKP-01 | Recoverability | An administrator shall be able to request a server-side database backup, and a backup shall be … | `server/backups.py`, `server/backup_restore.py` | — | `test_backup_restore_api.py` |
| NFR-PRIV-01 | Privacy | An electronic vote shall not be linkable to an elector, a voting session, a staff account or a … | Inspection of table `electronic_votes` and of the terminal's journal file (TC-EPL-14) | TC-EPL-14 | — |

## 3. Coverage summary and gaps

| Measure | Value |
| --- | --- |
| Functional requirements | 169 |
| … with at least one manual test case | 107 |
| … with at least one automated test listed | 97 |
| … with no test case listed | 21 |
| Non-functional requirements | 17 |
| … with no test case listed | 6 |
| Manual test cases defined | 100 |
| Manual test cases executed | `TODO(group)`: fill in after execution |
| Automated tests cited by name | 89 of 1,009 in the former suite |

Functional requirements with no test case listed. Each person in charge should either add a
manual test case or name the automated test that covers it:

| Requirement | Summary | Owner |
| --- | --- | --- |
| FR-SYS-01 | Reject every request that does not carry a valid session, except sign-in and the health … | Dennis |
| FR-SYS-02 | Allow an operational user to read and write only the stations assigned to that user. | Dennis |
| FR-SYS-07 | Record an audit event (actor, action, time) for sign-in, sign-out, password change and … | Dennis |
| FR-POL-09 | Refuse polling entries until the administrator has saved the election schedule. | Dennis |
| FR-STK-08 | Record the return of unissued papers from a desk to the presiding officer, after which … | Harriet |
| FR-SNP-05 | Reject a snapshot time in the future. | Toby |
| FR-TUR-09 | Record how each figure was obtained: copied from the external register (normal) … | Toby |
| FR-CMP-05 | Assign each case to a reporting period by its received time and count the cases of each … | John |
| FR-CMP-08 | Export complaint statistics for the station and for one period as CSV and PDF. | John |
| FR-QUE-05 | Export the queue history as CSV and PDF. | John |
| FR-FBK-09 | Allow a correction of a confirmed activation or recovery only with a reason, and require … | Mody |
| FR-OUT-06 | Export the outage and paper reconciliation report as CSV and PDF. | Mody |
| FR-SPP-02 | Base each observation on one current and complete P(12) snapshot and take the ordinary … | Salina |
| FR-SPP-06 | Require every received series to be reported exactly once. | Salina |
| FR-ACC-04 | Reject a turnout period that ends after the special-paper observation. | Toby |
| FR-CNT-16 | Require a reason to correct a submitted F1 or F2 and keep the submitted revision; a … | Toby |
| FR-RCT-07 | Refuse a constituency recount when the result has changed since the Supervisor loaded it. | Lam |
| FR-FIN-03 | Refuse finalisation when the facts have changed since the Supervisor reviewed them. | Lam |
| FR-EPL-02 | Allow an e-polling election to be activated without issuing desks. A physical-ballot … | Dennis |
| FR-EPL-08 | Refuse a vote when the candidate list has changed since the session started, so that the … | Dennis |
| FR-EPL-16 | Let a Polling Officer assigned to the station ask for the status (pending, recorded … | Dennis |

Non-functional requirements with no test case listed: NFR-USA-01, NFR-USA-02, NFR-USA-03, NFR-PERF-01, NFR-PORT-01, NFR-MNT-01. Their verification
method is given in the "Measure" column; NFR-PERF-01 and NFR-USA-03 are targets that have not
been measured yet.

## 4. Backward traceability

Every manual test case names at least one requirement (test cases without a requirement: 0).
Every use case UC-01 to UC-11 belongs to one module document, and each functional requirement
table cites the server module or route that implements it, so each piece of code described in
this pack can be traced back to a requirement.

| Use case | Module document | Requirement groups |
| --- | --- | --- |
| UC-01 | 01 Login and layout | AUTH |
| UC-02 | 02 Polling times | POL |
| UC-03 | 03 Stock and allocations | STK |
| UC-04 | 04 Snapshots and turnout | SNP, TUR |
| UC-05 | 05 Complaints and queue | CMP, QUE |
| UC-06 | 06 Failure handling | FBK, OUT, REC |
| UC-07 | 07 Post-poll times | BOX |
| UC-08 | 08 Special papers | SPP |
| UC-09 | 09 Count reports | ACC, CNT |
| UC-10 | 10 Recount and completion | RCT, RES, FIN |
| UC-11 | 14 E-polling | EPL |
