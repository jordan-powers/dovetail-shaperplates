# Dovetail Shaperplates

This script will generate a 3d-printable flat plate with embedded Shaper dominos. It can then
be printed using multi-material 3d printing to produce a robust surface for tracking when using the
Shaper Origin handheld CNC router. The generated plates are bordered with dovetail joints so you can
easily combine multiple plates into a single work surface.

<!-- TODO: Add a photo -->

## Installation
This tool requires python and OpenSCAD.
1. Clone this repository.
```bash
git clone git@github.com:jordan-powers/dovetail-shaperplates.git
```

2. Install required python libraries.
```bash
pip install -r requirements.txt
```

3. Download OpenSCAD from the [OpenSCAD website](https://openscad.org/downloads.html).

4. Open `gen-domino-plates.py` with a text editor and update the `OPENSCAD_EXE` variable to point
at the OpenSCAD executable downloaded in step 3.
```python
OPENSCAD_EXE = Path(r"<path/to/openscad.exe>")
```


## Usage

```
usage: gen-domino-plates.py [-h] [--svg-only] [--clean] [--seed SEED] num_rows num_cols thickness num_plates

positional arguments:
  num_rows     number of rows of dominos
  num_cols     number of columns of dominos
  thickness    thickness of generated plate, in inches
  num_plates   how many unique plate patterns to generate

options:
  -h, --help   show this help message and exit
  --svg-only   skip running openscad
  --clean      remove any previously generated files
  --seed SEED
```

**Note:** Make sure you have configured the `OPENSCAD_EXE` variable to point at the OpenSCAD executable.
See [Installation](#installation) for more details.

Note that the OpenSCAD is not fast, and it frequently takes me ~10 mins per plate to generate.

## The Grid
The domino plates produced by this tool will align to a grid, with each cell measuring
36.9mm tall by 45.5mm wide. when generating a plate, you will specify the number of grid rows
and columns in the generated plate.

To maximize domino density, you will want to print the largest contiguous grid that
will fit on the build plate of your 3d printer, as dominos cannot be printed across dovetail joins.

Use these formulae to calculate the width and height of a given plate in millimeters.
```
width = num_cols * 45.5 + 10
height = num_rows * 36.9 + 10
```

To calculate the max plate that will fit in a given volume (e.g. your build plate), simply reverse
the formulae.
```
num_cols = floor((width - 10) / 45.5)
num_rows = floor((height - 10 / 36.9))
```
