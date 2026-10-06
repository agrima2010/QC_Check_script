import argparse
import csv
import sys

MIN_COVERAGE = 95.0
MAX_FAIL_RATE = 10.0

def check_qc_file(filepath):
    """Read the summary file"""
    rows = []
    with open(filepath) as f:
        file = csv.DictReader(f, delimiter=",")
        for row in file:
            rows.append(row)
        return rows

def get_origin(sample_name):
    """Get the origin from the sample name"""
    return sample_name[1]

def check_failed(row):
    """Return True if the sample fails the quality check."""
    coverage = float(row["pct_covered_bases"])
    qc_pass = row["qc_pass"].strip().upper()

    if coverage < MIN_COVERAGE:
        return True
    if qc_pass == "FALSE":
        return True
    return False

def summary_by_origin(rows):
    """Count total and failed samples for each origin."""
    summary = {}
    for row in rows:
        origin = get_origin(row["sample"])
        if origin not in summary:
            summary[origin] = {"total": 0, "failed": 0}
        summary[origin]["total"] += 1
        if check_failed(row):
            summary[origin]["failed"] += 1
    return summary

def fail_rate(counts):
    """Percentage of failed samples."""
    return counts["failed"] / counts["total"] * 100

def write_report(summary, output_path):
    """Write one line per origin to a tab-separated file."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["origin", "total", "failed", "fail_rate_pct", "alert"])
        for origin in sorted(summary):
            counts = summary[origin]
            rate = fail_rate(counts)
            alert = "YES" if rate > MAX_FAIL_RATE else "NO"
            writer.writerow([origin, counts["total"], counts["failed"],
                             f"{rate:.1f}", alert])
def main():
    parser = argparse.ArgumentParser(description="Weekly QC check per sample origin.")
    parser.add_argument("qc_file", help="QC metrics file")
    parser.add_argument("--report", default="qc_report.tsv",
                        help="where to save the summary (default: qc_report.tsv)")
    args = parser.parse_args()

    rows = check_qc_file(args.qc_file)
    summary = summary_by_origin(rows)
    write_report(summary, args.report)

    print(f"Checked {len(rows)} samples from {len(summary)} origins")
    alerts = []
    for origin in sorted(summary):
        counts = summary[origin]
        rate = fail_rate(counts)
        print(f"  {origin}: {counts['failed']}/{counts['total']} failed ({rate:.1f}%)")
        if rate > MAX_FAIL_RATE:
            alerts.append(origin)

    # Warnings go to stderr so a scheduler like cron can pick them up
    for origin in alerts:
        counts = summary[origin]
        print(f"WARNING: origin {origin} has {fail_rate(counts):.1f}% failed samples "
              f"(limit {MAX_FAIL_RATE:.0f}%)", file=sys.stderr)

    print(f"Report saved to {args.report}")

    # Exit code 2 tells whoever runs the script that something needs attention
    if alerts:
        sys.exit(2)

if __name__ == "__main__":
    main()


