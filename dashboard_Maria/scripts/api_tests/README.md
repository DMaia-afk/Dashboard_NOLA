API test scripts for Dashboard NOLA

How to run

- Ensure your Django dev server is running locally (default: http://localhost:8000)
- From the `dashboard_Maria/scripts/api_tests` folder run:

  powershell:
  & 'C:\Users\Dmaia-AFK\Desktop\dashboard_Backup\env\Scripts\python.exe' .\run_card_api_tests.py

Notes
- The helper `api_test_client.py` prefers the `requests` library if present; if not available it falls back to the Python standard library.
- The runner writes `api_test_report.json` summarizing status codes and a small brief for each endpoint.
