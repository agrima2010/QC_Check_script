# Weekly QC Check per Sample Origin

A small Python script that reads the weekly quality-metrics file from the virus consensus pipeline, counts how many samples **fail QC for each origin**, and raises a warning when an origin has too many failures. It is meant to be run automatically (for example from cron) each time a new quality file is produced.

## What counts as a failed sample

A sample fails if **either** is true:

- `pct_covered_bases` is below **95 %**
- `qc_pass` is `FALSE` (case-insensitive)

## What the script does

1. Reads the CSV quality file (`sample, pct_N_bases, pct_covered_bases, longest_no_N_run, num_aligned_reads, qc_pass`).
2. Takes the sample origin from the **second character** of the sample name (`DN-64554` → `N`). Origins are discovered from the data, so new origins are handled without code changes.
3. Counts total and failed samples per origin.
4. Writes a tab-separated report (`qc_report.tsv`).
5. Prints a summary to stdout.
6. For every origin with **more than 10 %** failed samples, prints a `WARNING` line to **stderr** and exits with **code 2**.

## How the user is notified

- **Warnings on stderr**, one line per origin above the limit.
- **Exit code 2** when at least one origin is above the limit (0 means all fine). A scheduler or monitoring tool can act on this.
- **Report file** with the latest numbers for every origin.

The script itself does not send email. A simple option is to let cron do it, since cron mails the output of a job to the user set in `MAILTO` (requires a working mail setup on the server).

## Requirements

- Python 3.8 or later
- No third-party packages for the script (standard library only)
- `pytest` for running the tests

## Usage

```bash
python qc_check_script.py samples.txt
python qc_check_script.py samples.txt --report results/week_40.tsv
```

| Argument | Description | Default |
|---|---|---|
| `qc_file` | Path to the QC metrics CSV | required |
| `--report` | Where to save the summary table | `qc_report.tsv` |

### Example run on the provided `samples.txt`

```
Checked 373 samples from 4 origins
  C: 20/80 failed (25.0%)
  D: 32/107 failed (29.9%)
  N: 27/96 failed (28.1%)
  T: 12/90 failed (13.3%)
Report saved to qc_report.tsv
```

stderr:

```
WARNING: origin C has 25.0% failed samples (limit 10%)
WARNING: origin D has 29.9% failed samples (limit 10%)
WARNING: origin N has 28.1% failed samples (limit 10%)
WARNING: origin T has 13.3% failed samples (limit 10%)
```

Exit code: `2`

### Report format (`qc_report.tsv`)

```
origin  total  failed  fail_rate_pct  alert
C       80     20      25.0           YES
D       107    32      29.9           YES
N       96     27      28.1           YES
T       90     12      13.3           YES
```

## Running it automatically (cron example)

Run every Monday at 08:00 and mail any warnings:

```cron
MAILTO=your.name@example.com
0 8 * * 1  cd /path/to/repo && python qc_check_script.py /path/to/latest/samples.txt --report /path/to/reports/qc_report.tsv
```

## Tests

Tests are in `test_qccheck_script.py` and use `pytest`.

```bash
pip install pytest
python -m pytest -v
```

| Test | What it checks |
|---|---|
| `test_get_origin_normal` | Origin is taken from the second character of the name |
| `test_get_origin_empty_name_crashes` | An empty sample name raises `IndexError` (documents current behaviour) |
| `test_fail_rate_half` | Fail rate is calculated as a percentage |
| `test_low_coverage_fails` | A sample with coverage below 95 % is flagged as failed |
| `test_check_qc_file_reads_rows` | The CSV is read into one row per sample |
| `test_main_prints_summary` | End-to-end run of `main()` on a small file prints the expected summary |

All 6 tests pass.

## Repository contents

```
qc_check_script.py        # the QC check script
test_qccheck_script.py    # pytest tests
samples.txt               # example input (373 samples)
README.md
```

## Known limitations and possible improvements

- Input validation is minimal: a missing column, a non-numeric coverage value or a sample name shorter than two characters will stop the script with a Python error rather than a friendly message.
- The thresholds (95 % coverage, 10 % failure rate) are constants at the top of the script, not command-line options.
- Notification is limited to stderr, the exit code and the report file. Email or Slack sending could be added.
- Test coverage could be extended to the alert logic, the exit code and the report file contents.