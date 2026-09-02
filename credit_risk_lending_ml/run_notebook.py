"""
run_notebook.py

Executes credit_risk_analysis.ipynb end to end (in the current working
directory, so relative paths like "credit_applicants.csv" and "charts/"
resolve correctly), and writes the executed notebook back to disk with
real outputs.

Run:
    python run_notebook.py
"""

import nbformat
from nbclient import NotebookClient

NB_PATH = "credit_risk_analysis.ipynb"

nb = nbformat.read(NB_PATH, as_version=4)
client = NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": "."}})
client.execute()

with open(NB_PATH, "w") as f:
    nbformat.write(nb, f)

print(f"Executed and saved {NB_PATH}")
