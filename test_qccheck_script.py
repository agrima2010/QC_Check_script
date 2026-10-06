import pytest
import sys
import qc_check_script
from qc_check_script import get_origin
from qc_check_script import fail_rate
from qc_check_script import check_failed
from qc_check_script import check_qc_file


def test_get_origin_normal():
    assert get_origin("DN-64554") == "N"

def test_fail_rate_half():
    assert fail_rate({"failed": 5, "total": 10}) == 50.0

def test_low_coverage_fails():
    row = {"sample": "DN-1", "pct_covered_bases": "80.0", "qc_pass": "TRUE"}
    assert check_failed(row) == True

def test_get_origin_empty_name_crashes():
    with pytest.raises(IndexError):
        get_origin("")

def test_check_qc_file_reads_rows(tmp_path):
    # 1. Create a small fake input file
    path = tmp_path / "samples.txt"
    path.write_text("sample,pct_covered_bases,qc_pass\nDN-1,99.0,TRUE\n")

    # 2. Run the function
    rows = check_qc_file(path)

    # 3. Check the result
    assert len(rows) == 1
    assert rows[0]["sample"] == "DN-1"

def test_main_prints_summary(tmp_path, monkeypatch, capsys):
    path = tmp_path / "samples.txt"
    path.write_text("sample,pct_covered_bases,qc_pass\nDN-1,99.0,TRUE\n")

    monkeypatch.setattr(sys, "argv", ["qc_check.py", str(path),
                                      "--report", str(tmp_path / "r.tsv")])
    qc_check_script.main()

    printed = capsys.readouterr().out
    assert "Checked 1 samples from 1 origins" in printed