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
usage: gen-domino-plates.py [-h] [--svg-only] [--clean] [--start-domino START_DOMINO]
                            num_rows num_cols thickness num_plates

positional arguments:
  num_rows              number of rows of dominos
  num_cols              number of columns of dominos
  thickness             thickness of generated plate, in inches
  num_plates            how many unique plate patterns to generate

options:
  -h, --help            show this help message and exit
  --svg-only            skip running openscad
  --clean               remove any previously generated files
  --start-domino START_DOMINO
                        the hex id of the first domino to generate
```

**Note:** Make sure you have configured the `OPENSCAD_EXE` variable to point at the OpenSCAD executable.
See [Installation](#installation) for more details.

Note that the OpenSCAD is not fast, and it frequently takes me ~10 mins per plate to generate.

## The Grid
The domino plates produced by this tool will align to a grid, with each cell measuring
34.57mm tall by 45.5mm wide. When generating a plate, you will specify the number of grid rows
and columns in the generated plate.

To maximize domino density, you will want to print the largest contiguous grid that
will fit on the build plate of your 3d printer, as dominos cannot be printed across dovetail joins.

Use these formulae to calculate the width and height of a given plate in millimeters.
<!-- width = num_cols * (domino_width + domino_spacing) + dovetail_depth >
<!-- height = num_rows * 2 * (domino_height + (dovetail_depth * tan(90 deg - dovetail_angle))) + dovetail_depth -->
```
width = num_cols * 45.5 + 7.9375
height = num_rows * 34.5654 + 7.9375
```

To calculate the max plate that will fit in a given volume (e.g. your build plate), simply reverse
the formulae.
```
num_cols = floor((width - 7.9375) / 45.5)
num_rows = floor((height - 7.9375 / 34.5654))
```

## Domino IDs
Every unique domino is assigned an id, represented as a 4-digit hexadecimal number.
When generating a grid, dominos are generated sequentially; for example a grid containing 6 dominos
starting at domino `000c` would contain dominos `000c`, `000d`, `000e`, `000f`, `0010`, and `0011`.
When a grid with 3 or more columns is generated, the id of the first domino is embedded in the
upper-left corner. This is useful both to regenerate identical replacement grids, and to guarantee
grids contain unique dominos.

### Regenerating an Existing Grid
To regenerate a grid, pass the hex id from the original grid into the `--start-domino` flag. Ensure
you specify the same grid size (`num_rows` and `num_cols`).

For example, to regenerate a 5x5 grid with a start domino id of 000a and a thickness of 1/16",
use this command:
```bash
python3 gen-domino-plates.py 5 5 1/16 1 --start-domino 000a
```

### Generating a Unique Grid (Automatic)
When generating a grid, the program will look for existing grids in the `/svgs` folder and ensure
that the newly generated grid does not use dominos already in use by existing grids. Simply run the
program as normal and all produced grids will be unique.

### Generating a Unique Grid (Manual)
It is also possible to avoid conflicts with some other grids that are not present in the `/svgs`
folder.

To generate a unique grid, first start by looking through your existing grids and identifying the
one with the highest id. Note that this includes the grids present in the `/svgs` folder: using
manual uniqueness disables the automatic checking.

Once you have identified the highest-id grid, count the number of dominos and add the
domino count to the id. Finally, pass the result to the `--start-domino` flag.

For example, let's say I want to generate a new 5x5 grid. I look through my current grids, and I find
that the highest id grid is a 1x3 grid with 6 dominos and id 0010. I would generate the next plate
using the command:
```bash
python3 gen-domino-plates.py 5 5 1/16 1 --start-domino 0016
```

