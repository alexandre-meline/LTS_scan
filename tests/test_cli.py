import subprocess
import json
import csv
import tempfile
from pathlib import Path


def test_lts_scan_json_output():
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = Path(temp_dir) / "hosts.txt"
        output_file = Path(temp_dir) / "results.json"

        input_file.write_text("github.com\n")

        result = subprocess.run(
            [
                "poetry", "run", "lts-scan",
                "--input", str(input_file),
                "--output", str(output_file),
                "--format", "json"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Error: {result.stderr}"

        assert output_file.exists(), "Le fichier de sortie n'existe pas"

        with open(output_file) as f:
            data = json.load(f)

        assert isinstance(data, list), "The JSON output should be a list"
        assert len(data) > 0, "The JSON output is empty"
        assert "host" in data[0], "The 'host' field is missing in the response"


def test_lts_scan_csv_output():
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = Path(temp_dir) / "hosts.txt"
        output_file = Path(temp_dir) / "results.csv"

        input_file.write_text("github.com\n")

        result = subprocess.run(
            [
                "poetry", "run", "lts-scan",
                "--input", str(input_file),
                "--output", str(output_file),
                "--format", "csv"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Error: {result.stderr}"

        assert output_file.exists(), "The CSV file was not created"

        with open(output_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            assert len(rows) > 0, "No lines in the CSV"
            assert "host" in rows[0], "Missing 'host' column in CSV"
            assert rows[0]["host"] == "github.com", "Incorrect domain name in CSV"
