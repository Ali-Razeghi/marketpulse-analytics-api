# Illustrative mockups

The scripts in this folder generate the images under `docs/images/`. They are
**illustrative**: they render realistic-looking screens from *hard-coded sample
data* (`data.py`), not from a running server.

- `01`, `02`, `03`, `05`, `07` show the **real API contract** — the JSON these
  scripts display matches exactly what the endpoints return.
- `04`, `06`, `08` are **dashboard concepts**. The current project is a
  backend/API and does not ship a dashboard UI; these show what a future
  visualisation layer (e.g. Streamlit or React) consuming this API could look
  like. They are not produced by application code.

To regenerate the images:

```bash
pip install matplotlib
python scripts/mockups/generate_terminal.py
python scripts/mockups/generate_dashboards.py
```

The scripts write PNGs to `/mnt/user-data/outputs` by default; edit the `OUT`
constant to change the destination.
