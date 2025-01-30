import argparse
from random import randint
from svgwrite import Drawing
from pathlib import Path
import subprocess
import json
import xml.etree.ElementTree as ET
import hashlib

OPENSCAD_EXE = Path(r"C:\Users\jordan\Downloads\OpenSCAD-2025.01.29-x86-64\openscad.exe")

parser = argparse.ArgumentParser()
parser.add_argument("num_rows", type=int, help="number of rows of dominos")
parser.add_argument("num_cols", type=int, help="number of columns of dominos")
parser.add_argument("thickness", type=str, help="thickness of generated plate, in inches")
parser.add_argument("num_plates", type=int, help="how many unique plate patterns to generate")
parser.add_argument("--svg-only", action="store_true", help="skip running openscad")

args = parser.parse_args()

dovetail_depth = 10

domino_horiz_spacing = 2.25
domino_width = 43
domino_height = 12.7

thickness_in = eval(args.thickness)
thickness_mm = thickness_in * 25.4

# Adapted from https://github.com/augiev/Shaper-Dominos
dpi = 96
scale = dpi/25.4
fillet_rad = 2.5*scale
circle_rad = 1.25*scale
circle_grid = 5.08*scale
rect_w = domino_width*scale
rect_h = domino_height*scale

border_w = domino_horiz_spacing*scale
border_h = (dovetail_depth - domino_height/2) *scale
xoff = rect_w/2 + (domino_horiz_spacing/2)*scale
yoff = rect_h/2 + dovetail_depth*scale

xoff_extra = (domino_horiz_spacing + domino_width - dovetail_depth) * scale / 2

def generate(d_outline, d_dots, rows, cols, previous=set()):
    assert rows > 0 and cols > 0

    extra_rows = rows-1

    num_domino = (rows * cols) + (extra_rows * (cols-1))

    vals = set()
    while len(vals) < (num_domino):
        rand = randint(0, 65536)
        rand |= 1 | (1<<7) | (1<<8) | (1<<15)
        top = bin(rand)[3:9]
        bottom = bin(rand)[11:17]

        # require 10 total dots
        if bin(rand).count('1') != 10:
            continue

        # discard if dots are in a rotationally-symmetric pattern
        if top == ''.join(reversed(bottom)):
            continue

        # check if an exact duplicate exists
        if not rand in vals and not rand in previous:
            vals.add(rand)


    row_col = []
    for r in range(rows + extra_rows):
        if r % 2 == 0:
            thisrow_cols = cols
        else:
            thisrow_cols = cols-1
        for c in range(thisrow_cols):
            row_col.append((r,c))
    gen = zip(row_col, vals)

    for (r, c), spots in gen:
        xoff2 = xoff + c*(rect_w + border_w)
        yoff2 = yoff + r*(rect_h + border_h)

        if r % 2 == 1:
            xoff2 += xoff_extra

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

previous = set()

max_count = 903 # total number of valid fiducials (based on exhaustive search)

requested_count = args.num_rows*args.num_cols*args.num_plates
if requested_count > max_count:
    print(f'error, only {max_count} fiducials exist; requested {requested_count}')
    exit(1)

svg_dir = Path.cwd() / 'svgs'
if not svg_dir.is_dir():
    svg_dir.mkdir()

# Load previous
ns = {'svg':'http://www.w3.org/2000/svg'}
doc_count = 0
for f in svg_dir.glob("*.svg"):
    root = ET.parse(f).getroot()
    desc = root.find('svg:desc', ns)
    if desc is None:
        continue
    try:
        values = json.loads(desc.text)
        if 'dominos' in values:
            previous.update(values['dominos'])
            doc_count += 1
    except json.decoder.JSONDecodeError:
        pass

if len(previous) > 0:
    print(f"Excluding {len(previous)} dominos from {doc_count} previously-generated documents")

hashes = []

for i in range(args.num_plates):
    dwg_outline = Drawing(filename="nopath.svg", debug=True)
    dwg_dots = Drawing(filename="nopath.svg", debug=True)
    values = generate(dwg_outline, dwg_dots, args.num_rows, args.num_cols, previous)
    previous.update(values)
    hash = hashlib.sha256(','.join(str(v) for v in values).encode('utf-8')).hexdigest()
    hashes.append(hash)
    meta = json.dumps({
        "dominos": list(values),
        "hash": hash
    })
    dwg_outline.set_desc(desc=meta)
    dwg_dots.set_desc(desc=meta)
    outpath_outline = svg_dir / f'{args.num_rows}_{args.num_cols}_{hash[:8]}_outline.svg'
    outpath_dots = svg_dir / f'{args.num_rows}_{args.num_cols}_{hash[:8]}_dots.svg'
    dwg_outline.saveas(outpath_outline, pretty=True)
    dwg_dots.saveas(outpath_dots, pretty=True)

if args.svg_only:
    exit(0)

stl_dir = Path.cwd() / "stls"
if not stl_dir.is_dir():
    stl_dir.mkdir()

for i in range(args.num_plates):
    print( "\n\n+===================+")
    print(f"| Generating file {i} |")
    print( "+===================+\n")
    for layer, lid in (('dominos', 0), ('dovetails', 1)):
        hash = hashes[i]
        outfile = stl_dir / f"{thickness_in:.2f}_{args.num_rows}_{args.num_cols}_{hash[:8]}_{layer}.stl"
        subprocess.run([
            OPENSCAD_EXE,
            "-o", outfile,
            "-D", f"num_rows={args.num_rows}",
            "-D", f"num_cols={args.num_cols}",
            "-D", f"thickness={thickness_mm}",
            "-D", f"label=\"{args.thickness}\\\" - {args.num_rows}x{args.num_cols} - {hash[:8]}\"",
            "-D", f"fid=\"{hash[:8]}\"",
            "-D", f"selector={lid}",
            "dovetail-shaperplates.scad"
        ], cwd=Path(__file__).parent)
