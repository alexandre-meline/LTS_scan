# LTS scan

**LTS scan** is a command-line tool written in Python that leverages the [Qualys SSL Labs API](https://api.ssllabs.com) to scan and evaluate SSL/TLS configurations of websites.  
It supports multiple hosts, retry logic, and output in CSV or JSON formats.

---

## ✨ Features

- Asynchronous scans using `asyncio` and `aiohttp`
- Retry mechanism for API failures
- Supports both CSV and JSON output
- Automatically waits until scan status is `READY` or `ERROR`
- Command-line options for customization
- Clear and readable logs

---

## 🚀 Installation

We recommend using [Poetry](https://python-poetry.org/) for managing dependencies and environments.

```bash
git clone https://github.com/alexandre-meline/LTS_scan.git
cd lts-scan
poetry install
```

## 🧪 Usage

Create a hosts.txt file with one domain per line:

```bash
google.com
github.com
expired.badssl.com
```

```bash
lts-scan --input hosts.txt --output results.csv
```

Then run the tool:

```bash
lts-scan --input hosts.txt --output results.csv
```

You can customize the output format:

```bash
lts-scan --input hosts.txt --output results.json --format json
```

### 🔧 Command-line options

| Option | Description | Default |
| --- | --- | --- |
| `--input` | Path to the input file containing hosts |_required_ |
| `--output` | Path to the output file | _required_ |
| `--format` | Output format: `csv` or `json` | `csv` |
| `--retries` | Number of retry attempts on request failure | `3` |
| `--delay` | Delay (in seconds) between retries | `10` |

## 📄 Output Examples

CSV

```csv
host,status,startTime,testTime,ipAddress,grade
example.com,READY,1681234567890,1681237890123,93.184.216.34,A
```

JSON

```json
[
  {
    "host": "example.com",
    "status": "READY",
    "startTime": 1681234567890,
    "testTime": 1681237890123,
    "endpoints": [
      {
        "ipAddress": "93.184.216.34",
        "grade": "A"
      }
    ]
  }
]
```

## 📋 License

This project is licensed under the MIT License.

## 🙌 Acknowledgements

- [Qualys SSL Labs API](https://www.ssllabs.com/)

## 💡 Future Improvements

- Parallel host scanning
- Export to HTML or PDF