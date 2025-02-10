import argparse
import random
from svgwrite import Drawing
from pathlib import Path
import subprocess
import json
import xml.etree.ElementTree as ET
import shutil
import math

OPENSCAD_EXE = Path(r"C:\Users\jordan\Downloads\OpenSCAD-2025.01.29-x86-64\openscad.exe")

parser = argparse.ArgumentParser()
parser.add_argument("num_rows", type=int, help="number of rows of dominos")
parser.add_argument("num_cols", type=int, help="number of columns of dominos")
parser.add_argument("thickness", type=str, help="thickness of generated plate, in inches")
parser.add_argument("num_plates", type=int, help="how many unique plate patterns to generate")
parser.add_argument("--svg-only", action="store_true", help="skip running openscad")
parser.add_argument("--clean", action="store_true", help="remove any previously generated files")
parser.add_argument("--start-domino", type=str, help="the hex id of the first domino to generate")

args = parser.parse_args()

if not args.svg_only and not OPENSCAD_EXE.is_file():
    print("error: could not locate openscad.exe")
    exit(1)

dovetail_depth = (5/16) * 25.4
dovetail_angle = 60

domino_horiz_spacing = 2.25
domino_width = 43
domino_height = 12.7

thickness_in = eval(args.thickness)
thickness_mm = thickness_in * 25.4

grid_height = (domino_height + dovetail_depth*math.tan(math.radians(90-dovetail_angle))) * 2

svg_dir = Path.cwd() / 'svgs'
if args.clean and svg_dir.is_dir():
    shutil.rmtree(svg_dir)
if not svg_dir.is_dir():
    svg_dir.mkdir()

stl_dir = Path.cwd() / "stls"
if args.clean and stl_dir.is_dir():
    shutil.rmtree(stl_dir)
if not stl_dir.is_dir():
    stl_dir.mkdir()

# Adapted from https://github.com/augiev/Shaper-Dominos
class DominoGenerator:
    MAX_COUNT = 903 # total number of valid fiducials (based on exhaustive search)
    def __init__(self, start_domino: int = 0):
        self.generator = random.Random("bd965e0a")
        self.prev = set()

        while len(self.prev) < start_domino:
            next(self)

    @property
    def next_id(self):
        return len(self.prev)

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.prev) >= DominoGenerator.MAX_COUNT:
            raise StopIteration

        while True:
            rand = self.generator.randint(0, 65536)
            rand |= 1 | (1<<7) | (1<<8) | (1<<15)
            top = bin(rand)[3:9]
            bottom = bin(rand)[11:17]

            # require 10 total dots
            if bin(rand).count('1') != 10:
                continue

            # discard if dots are in a rotationally-symmetric pattern
            if top == ''.join(reversed(bottom)):
                continue

            if rand in self.prev:
                continue

            self.prev.add(rand)

            return rand

dpi = 96
scale = dpi/25.4
fillet_rad = 2.5*scale
circle_rad = 1.25*scale
circle_grid = 5.08*scale
rect_w = domino_width*scale
rect_h = domino_height*scale

border_w = domino_horiz_spacing*scale
border_h = ((grid_height/2) - domino_height) *scale
xoff = rect_w/2 + (domino_horiz_spacing/2)*scale
yoff = (grid_height/2)*scale

def generate(d_outline, d_dots, rows, cols, generator: DominoGenerator):
    assert rows > 0 and cols > 0

    num_domino = ((rows*2 - 1) * cols)

    vals = []
    while len(vals) < (num_domino):
        vals.append(next(generator))

    row_col = []
    for r in range(rows*2-1):
        for c in range(cols):
            row_col.append((r,c))
    gen = zip(row_col, vals)

    for (r, c), spots in gen:
        xoff2 = xoff + c*(rect_w + border_w)
        yoff2 = yoff + r*(rect_h + border_h)

        if r % 2 == 1:
            xoff2 += dovetail_depth*scale

        # draw rounded rectangle
        cmds = [
            'M {} {}'.format(-rect_w/2 + fillet_rad + xoff2, rect_h/2 + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, -rect_w/2 + xoff2, rect_h/2 - fillet_rad + yoff2),
            'L {} {}'.format(-rect_w/2 + xoff2, -rect_h/2 + fillet_rad + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, -rect_w/2 + fillet_rad + xoff2, -rect_h/2 + yoff2),
            'L {} {}'.format(rect_w/2 - fillet_rad + xoff2, -rect_h/2 + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, rect_w/2 + xoff2, -rect_h/2 + fillet_rad + yoff2),
            'L {} {}'.format(rect_w/2 + xoff2, rect_h/2 - fillet_rad + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, rect_w/2 - fillet_rad + xoff2, rect_h/2 + yoff2),
            'z'
            ]

        d_outline.add(d_outline.path(d=''.join(cmds), fill='black', stroke='none'))

        for i in range(8):
            if spots & (1<<i):
                d_dots.add(d_dots.circle(center=((-3.5 + i)*circle_grid + xoff2, circle_grid/2 + yoff2), r=circle_rad, fill='black'))
            if spots & (1<<(i+8)):
                d_dots.add(d_dots.circle(center=((-3.5 + i)*circle_grid + xoff2, -circle_grid/2 + yoff2), r=circle_rad, fill='black'))
    return vals

requested_count = args.num_rows*args.num_cols*args.num_plates
if requested_count > DominoGenerator.MAX_COUNT:
    print(f'error, only {DominoGenerator.MAX_COUNT} fiducials exist; requested {requested_count}')
    exit(1)

if args.start_domino is not None:
    start_domino = int(args.start_domino, 16)
else:
    start_domino = 0
    # Load previous
    ns = {'svg':'http://www.w3.org/2000/svg'}
    for f in svg_dir.glob("*.svg"):
        root = ET.parse(f).getroot()
        desc = root.find('svg:desc', ns)
        if desc is None:
            continue
        try:
            values = json.loads(desc.text)
            if 'start_id' in values and 'num_dominos' in values:
                start_domino = max(start_domino, values['start_id'] + values['num_dominos'])
        except json.decoder.JSONDecodeError:
            pass

    print(f'No start domino specified, starting from {start_domino}')

generator = DominoGenerator(start_domino)

start_ids = []

for i in range(args.num_plates):
    dwg_outline = Drawing(filename="nopath.svg", debug=True)
    dwg_dots = Drawing(filename="nopath.svg", debug=True)

    start_id = generator.next_id
    start_id_str = '{:>04x}'.format(start_id)
    start_ids.append(start_id_str)

    values = generate(dwg_outline, dwg_dots, args.num_rows, args.num_cols, generator)

    meta = json.dumps({
        "dominos": values,
        "start_id": start_id,
        "num_dominos": len(values)
    })
    dwg_outline.set_desc(desc=meta)
    dwg_dots.set_desc(desc=meta)

    outpath_outline = svg_dir / f'{args.num_rows}_{args.num_cols}_{start_id_str}_outline.svg'
    outpath_dots = svg_dir / f'{args.num_rows}_{args.num_cols}_{start_id_str}_dots.svg'
    dwg_outline.saveas(outpath_outline, pretty=True)
    dwg_dots.saveas(outpath_dots, pretty=True)

if args.svg_only:
    exit(0)

for i in range(args.num_plates):
    print( "\n\n+===================+")
    print(f"| Generating file {i} |")
    print( "+===================+\n")
    for layer, lid in (('dominos', 0), ('dovetails', 1)):
        start_id_str = start_ids[i]
        outfile = stl_dir / f"{thickness_in:.2f}_{args.num_rows}_{args.num_cols}_{start_id_str}_{layer}.stl"
        subprocess.run([
            OPENSCAD_EXE,
            "-o", outfile,
            "-D", f"num_rows={args.num_rows}",
            "-D", f"num_cols={args.num_cols}",
            "-D", f"thickness={thickness_mm}",
            "-D", f"dovetail_angle={dovetail_angle}",
            "-D", f"label=\"{args.thickness}\\\" - {args.num_rows}x{args.num_cols} - {start_id_str}\"",
            "-D", f"fid=\"{start_id_str}\"",
            "-D", f"selector={lid}",
            "dovetail-shaperplates.scad"
        ], cwd=Path(__file__).parent)
