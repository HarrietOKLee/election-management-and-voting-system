# 12. Testing strategy and test record

Status of this document: the strategy and the test cases are written; the test cases have
not been executed by the authors of this pack. Every "Result" cell is `TODO(Name)` until the
person in charge has run the test and recorded what happened. Do not copy an expected result
into a result cell without running the test.

## 1. Goals

| Goal (Lecture 8) | What it means for Election Desk |
| --- | --- |
| Validation testing: show that the system meets its requirements | At least one test for every requirement in documents 00 to 10 and 14; the link is kept in document 11 |
| Defect testing: find inputs that make the system behave incorrectly | Invalid partitions, boundary values, wrong role, wrong order of steps, repeated and concurrent commands |

Testing can show the presence of errors, not their absence. For an election system the most
damaging failures are a wrong total, a lost record and an unauthorised change, so the test
effort is concentrated on arithmetic rules, revisions and role checks.

## 2. Test levels

| Level (Lecture 8) | Object under test | Technique | Tool | Who |
| --- | --- | --- | --- | --- |
| Unit testing | Pure functions and classes: serial-number ranges (`stock_serials.py`), totals (`counting_totals.py`), turnout derivation (`turnout_basis.py`), password policy (`security.py`) | Partition testing, boundary values | pytest | Developer |
| Component (interface) testing | One API router with a real MySQL database: every route with valid input, invalid input, wrong role, stale revision, repeated request | Requirements-based; interface errors (misuse, misunderstanding, timing) | pytest + FastAPI `TestClient` (`*_api.py`) | Developer |
| Component testing, client | One desktop controller or one QML page against a test server | State after each signal; error message shown | pytest + PySide6 (`*_desktop.py`, `test_qml_*.py`) | Developer |
| System testing | Whole system through the user interface: use cases UC-01 to UC-11 as scenarios across roles | Scenario / use-case testing | Manual, on a rehearsal copy of the demo server | Person in charge of each module |
| Release testing | The packaged v1.1.0 client on Windows and macOS against a Docker server; non-functional requirements | Requirements-based; installation; performance target | Manual + GitHub Actions `build-desktop.yml` | All |
| User (acceptance) testing | The walkthroughs of `demo/README.md` (live e-polling and the three paper-ballot stages) performed by a group member who did not work on that module | Alpha testing against the reference manual | Manual | All |
| Regression testing | Everything above after a change | Re-run the automated suite; re-run the manual cases of the changed module | pytest; this document | Developer |

Static checks complement testing: `ruff` and `mypy --strict` are configured in
`pyproject.toml` (NFR-MNT-01).

## 3. Automated tests: history and present state

This section describes what is in the Git history of the `main` branch. It must be stated
honestly in the report. Commit identifiers are those of the history published with v1.1.0 on
21 November 2026; identifiers quoted in earlier versions of this pack (`e886c76`, `04e57ea`)
no longer exist.

| Fact | Evidence |
| --- | --- |
| Up to commit `c68fb54` the repository had a `tests/` directory with 270 test files containing 1,009 test functions (110 files `*_api.py`, 42 files `test_qml_*.py`, the rest desktop-controller, report and support tests) and 25 support files | `git ls-tree -r --name-only c68fb54 -- tests` |
| The tests ran against a disposable MySQL database, never SQLite | `tests/conftest.py` at `c68fb54`, first line |
| The next commit, `6b0b4a5` ("add resumable election demos and prepare public submission"), deleted `tests/`, deleted `src/election/dev.py` and the `mysql-dev` and `tls-dev` commands of `manage.py` (the helpers that start the test database and create the test certificates), removed `pytest`, `pytest-cov`, `httpx` and `pypdf` from the `dev` dependency group and removed the pytest settings from `pyproject.toml` | `git show --stat 6b0b4a5`; `git diff c68fb54 6b0b4a5 -- pyproject.toml src/election/manage.py` |
| Between `c68fb54` and release v1.0.0, 127 files under `src/` changed; between `c68fb54` and release v1.1.0, 144 files | `git diff --shortstat c68fb54 v1.0.0 -- src`; `git diff --shortstat c68fb54 v1.1.0 -- src` |
| Releases v1.0.0 and v1.1.0 therefore contain no automated tests | `git ls-tree --name-only v1.1.0` |
| E-polling (v1.1.0, 59 files changed) was written after the tests were removed. No automated test for it exists anywhere in the history | `git diff --stat v1.0.0 v1.1.0` |

Consequences:

- The automated tests named in documents 01 to 10 are evidence of how the system was tested
  during development. They are not part of the submitted release.
- Because source files changed in and after the commit that removed the tests, the old tests
  cannot be assumed to pass on v1.1.0. Some will need to be updated.
- E-polling is covered by manual test cases only (document 14).

Recommended action (change request CR-02 in document 13), to be done by the repository owner:

```sh
git checkout -b restore-tests
git checkout c68fb54 -- tests src/election/dev.py
# put back in src/election/manage.py: the mysql-dev and tls-dev commands
#   (git diff c68fb54 6b0b4a5 -- src/election/manage.py shows the removed lines)
# put back in pyproject.toml: pytest, pytest-cov, httpx, pypdf>=6.21.2 in the dev group, and
#   [tool.pytest.ini_options] testpaths = ["tests"], pythonpath = ["src"], addopts = "-ra"
uv lock && uv sync
uv run pytest -q               # needs the test MySQL database and TLS files described in tests/conftest.py
```

These commands were written from the Git history and have not been run by the authors of this
pack. Then record the outcome in the table below. If a full restoration is not possible before
the deadline, restore at least the API tests of one module per person and report the numbers
truthfully. New tests for e-polling are change request CR-13.

| Item | Value |
| --- | --- |
| Date of run | Not restored in v1.1.0 (CR-02); no automated run is claimed |
| Commit tested | Not restored in v1.1.0 (CR-02); no automated run is claimed |
| Tests collected | Not restored in v1.1.0 (CR-02); no automated run is claimed |
| Passed / failed / errors / skipped | Not restored in v1.1.0 (CR-02); no automated run is claimed |
| Statement coverage (`pytest --cov=src/election`) | Not restored in v1.1.0 (CR-02); no automated run is claimed |
| Failures explained by intended changes after `c68fb54` | Not restored in v1.1.0 (CR-02); no automated run is claimed |

## 4. Manual system tests

### 4.1 Test environment

Since v1.1.0 `scripts/prepare_demo.py` builds two different fictional elections
(`demo/README.md`). The test cases of documents 01 to 10 need the paper-ballot demo; the test
cases of document 14 need the e-polling demo.

| Item | Paper-ballot demo (documents 01 to 10) | E-polling demo (document 14) |
| --- | --- | --- |
| Start command | `prepare_demo.py start --voting-method paper --stage polling` | `prepare_demo.py start` |
| Default port and directory | 8444, `.runtime/demo/` | 8445, `.runtime/demo-e-polling/` |
| Stages | `polling`, `counting`, `results` | `polling` only |
| Accounts | `demo_admin`, `demo_polling`, `demo_counting`, `demo_supervisor` | the same four and `demo_epolling` (voting terminal) |
| Data | Station Harbour Community Hall (`DEMO-S01`), desks D01 and D02, 520 papers received, 300 issued, votes 170 / 125 / invalid 5 | Same station with an approved opening; candidates Alex Chan and Jamie Wong; no votes |

Server: a Docker Compose project started by the script. Client: the command below or the
v1.1.0 package. Passwords: `<directory>/ACCOUNTS.md`.

The client starts in Traditional Chinese. Select English in the language box at the top right
before following a test case, because the steps quote the English labels.

Shared e-polling server. From 21 November 2026 the repository owner also hosts one e-polling
demo server (v1.1.0) on the internet for the group. No Docker is needed: start the v1.1.0
package, type the server address in the "Server address" box of the sign-in page and sign in
with a demo account. The address and the passwords are sent in the group chat and are not
stored in Git. This server has one election, with voting method e-polling, so:

| Can be run on the shared server | Cannot be run on the shared server |
| --- | --- |
| Document 14, except TC-EPL-10 (needs a server stop) and TC-EPL-13 (ends the voting service for everybody) | All paper-only test cases: documents 03, 04, 06 (fallback), 07, 08, 09 and 10 |
| Read-only checks of documents 01, 02 and 05; adding complaints and queue observations | Password changes, account changes, closure records and any other step that locks out or stops the other members |

The data on the shared server belongs to everybody: write down the supervisor total before a
case, because another member may be voting at the same time.

Rules for running the manual tests:

1. Use a rehearsal copy, not the demo kept for the video. Stages only advance, there is no
   reset, and the importer remembers the revision numbers of the records it created; a manual
   amendment of a seeded record can make the next stage fail.

   Paper-ballot rehearsal copy (documents 01 to 10):

   ```sh
   uv run --locked python scripts/prepare_demo.py start --voting-method paper --directory .runtime/demo-rehearsal --port 8446 --stage polling
   uv run --locked --directory src python -m election.desktop --server https://localhost:8446 --ca ../.runtime/demo-rehearsal/ca.pem
   ```

   E-polling rehearsal copy (document 14):

   ```sh
   uv run --locked python scripts/prepare_demo.py start --directory .runtime/epolling-rehearsal --port 8447
   uv run --locked --directory src python -m election.desktop --server https://localhost:8447 --ca ../.runtime/epolling-rehearsal/ca.pem
   ```

   Without `--voting-method paper` the script starts the e-polling demo, in which the pages
   for stock, turnout, boxes and counting are hidden.

2. Run the test cases of one stage, then advance the paper-ballot copy with the same command
   and `--stage counting`. If the importer refuses to advance after manual changes, start a new
   copy in another directory and port directly at the stage needed.
3. For tests that need a state the importer does not provide (for example an approved count
   on an active election), perform the missing steps by hand as described in the module
   document.
4. Record for each test case: result (Pass / Fail), date, tester, build (v1.1.0 or commit),
   and a screenshot for the cases marked "+ screenshot". Store screenshots in
   `docs/evidence/<module>/TC-XXX-NN.png`.
5. A failed test is a finding, not an embarrassment. Record it in section 6 and raise a
   change request in document 13.

### 4.2 Test case inventory

| Module document | Person in charge | Test cases | Stage needed |
| --- | --- | --- | --- |
| 01 Login and layout | Rico | TC-AUTH-01 to 05 | any |
| 02 Polling times | Dennis | TC-POL-01 to 06 | polling |
| 03 Stock and allocations | Harriet | TC-STK-01 to 07 | polling |
| 04 Snapshots and turnout | Toby | TC-SNP-01 to 04, TC-TUR-01 to 05 | polling |
| 05 Complaints and queue | John | TC-CMP-01 to 05, TC-QUE-01 to 03 | polling |
| 06 Failure handling | Mody | TC-FBK, TC-OUT, TC-REC (8 cases) | polling |
| 07 Post-poll times | Lam | TC-BOX-01 to 08 | polling, counting |
| 08 Special papers | Salina | TC-SPP-01 to 06 | polling |
| 09 Count reports | Toby | TC-ACC-01 to 03, TC-CNT-01 to 13 and TC-CNT-05a | counting |
| 10 Recount and completion | Lam | TC-RES-01 to 03, TC-RCT-01 to 04, TC-FIN-01 to 05 | counting, results |
| 14 E-polling | Dennis | TC-EPL-01 to 14 | e-polling demo |

### 4.3 Test design techniques used

Partition testing (Lecture 8): inputs are divided into equivalence partitions and one value is
taken from the middle and from each boundary of every partition. Examples in this pack:

| Input | Partitions | Values chosen | Module |
| --- | --- | --- | --- |
| New password length | < 12 (invalid), 12 to 128 (valid), > 128 (invalid) | 11, 12, 128, 129 | 01 |
| Serial range of an allocation | inside received stock (valid), overlapping another desk (invalid), outside stock (invalid), from > to (invalid) | first and last serial of the range | 03 |
| Tendered papers issued (reserve 10) | negative, 0 to 10, above 10, not a whole number | −1, 0, 10, 11, 1.5 | 08 |
| Vote quantity on F1 | blank (not observed), negative, 0, positive whole number, non-integer | blank, −1, 0, 170, 1.5 | 09 |
| Event time | past (valid), now (boundary), future (invalid) | yesterday 09:00, tomorrow | 07 |
| Voting service state when a session starts | not open (invalid), open (valid), queued (valid), ended (invalid) | open, ended | 14 |

Testing guidelines applied: force every error message at least once; repeat the same input
(retry with the same request identifier, NFR-REL-02); use the wrong role for every write;
make arithmetic results too large and too small by one.

Scenario testing: use cases UC-01 to UC-10 form one end-to-end scenario, "one polling day
at Harbour Community Hall" (paper-ballot demo). UC-11 is a second scenario, "three electors
vote on a terminal while the supervisor watches the totals" (e-polling demo). Both are in the
script of the video (see `video/video-outline.md`).

## 5. Release and non-functional tests

| Requirement | Test | Result |
| --- | --- | --- |
| NFR-PORT-01 | Install the v1.1.0 Windows package and the macOS package on clean machines; sign in to the demo server | `TODO(group)` |
| NFR-SEC-01 | Start the client with a wrong `--ca` file | `TODO(group)`: expected, connection refused |
| NFR-USA-01 | Switch to 繁體中文, 简体中文 and English on three pages and export one PDF in each | `TODO(group)` |
| NFR-USA-03 | Time three members recording one queue observation | `TODO(group)`: target under 60 s |
| NFR-PERF-01 | Record response times of 20 requests from the client log or the browser tools of the API docs | `TODO(group)`: target 95% within 1 s |
| NFR-REL-03 | Save a record, restart the server container and the client, check the record | `TODO(group)` |
| NFR-BKP-01 | As `demo_admin` request a backup under "Server backups" | `TODO(group)` |
| NFR-MNT-01 | `uv run ruff check src` and `uv run mypy` | Pass: `ruff` reported "All checks passed" and `mypy` reported no issues in 202 source files (commit `f5105cb`, 2026-11-22) |
| NFR-PRIV-01 | TC-EPL-14; in addition, start the client with `ELECTION_CLIENT_STATE_DIR` set to an empty private folder (`chmod 700`), start a session, select a candidate, open the file `e-polling.pending` in that folder and check that it holds no candidate | `TODO(group)` |

## 6. Test execution summary

Fill in after execution. Numbers must come from the tables in the module documents.

| Module | Cases | Passed | Failed | Not run | Tester | Date |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | 5 | | | | Rico | |
| 02 | 6 | | | | Dennis | |
| 03 | 7 | | | | Harriet | |
| 04 | 9 | | | | Toby | |
| 05 | 8 | | | | John | |
| 06 | 8 | | | | Mody | |
| 07 | 8 | | | | Lam | |
| 08 | 6 | | | | Salina | |
| 09 | 17 | | | | Toby | |
| 10 | 12 | | | | Lam | |
| 14 | 14 | | | | Dennis | |
| Total | 100 | | | | | |

Defect log:

| No. | Test case | Observed behaviour | Severity | Change request | Status |
| --- | --- | --- | --- | --- | --- |
| `TODO(group)` | | | | | |

## 7. Limits of the testing

- No test with real election staff has been carried out; usability figures are targets.
- No load test beyond the demo data (one station, two desks).
- Security testing is limited to role checks, password rules and TLS verification; there has
  been no penetration test.
- E-polling has manual test cases only, and no test with more than one station.
- The manual test cases were derived from reading the source code of v1.0.0 and v1.1.0. Where the
  observed behaviour differs from the expected result, first check the expected result
  against the code, then decide whether it is a defect.
