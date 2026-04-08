# DuctCalc Pro

A much more complete ductwork takeoff + fabrication helper inspired by CAMduct-style workflows.

## New full program

Run:

```bash
python camduct_program.py
```

### Capabilities

- Fitting library: **Straight**, **Reducing Cone**, **Gored Elbow**, **Offset**.
- Live fabrication math per fitting:
  - Flat width/length
  - Area (sqft)
  - Weight (lb)
  - Labor hours
  - Material/labor/total cost
- Project workflow:
  - Customer / quote / project header
  - Multi-line takeoff table
  - By-thickness rollup summary
- Data interoperability:
  - Export CSV
  - Save/load full project JSON
  - Generate DXF patterns per fitting or batch
- Material library editor for thickness-specific $/sqft pricing.

## Dependencies

- Python 3.10+
- `ezdxf` (optional, only needed for DXF generation)

Install:

```bash
pip install ezdxf
```

## Legacy scripts still present

- `ductCalc.py` (CLI)
- `duct_gui.py` (older GUI)
- `d3gui.py` (simple GUI)
- `gored_flat_pattern.py` (utility)
