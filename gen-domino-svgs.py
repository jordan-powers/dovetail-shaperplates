import argparse
from random import randint
from svgwrite import Drawing
from pathlib import Path
import subprocess

OPENSCAD_EXE = Path(r"C:\Users\jordan\Downloads\OpenSCAD-2021.01-x86-64\openscad-2021.01\openscad.exe")

parser = argparse.ArgumentParser()
parser.add_argument("width", type=int, help="width of 3d printer build plate, in mm")
parser.add_argument("height", type=int, help="height of 3d printer build plate, in mm")
parser.add_argument("dovetail_depth", type=int, help="depth of dovetail, in mm")
parser.add_argument("thickness", type=float, help="thickness of generated plate, in mm")
parser.add_argument("num_plates", type=int, help="how many unique plate patterns to generate")
parser.add_argument("--svg-only", action="store_true", help="skip running openscad")

args = parser.parse_args()

domino_vert_spacing = 5
domino_horiz_spacing = 2.25
domino_width = 43
domino_height = 12.7
# dovetail_angle = max(math.radians(60), math.atan(args.dovetail_depth / domino_spacing))

num_rows = int((args.height - (args.dovetail_depth*2) + domino_vert_spacing) // (domino_height + domino_vert_spacing))
print(f"num_rows={num_rows}")

padding_height = (args.height - (args.dovetail_depth*2) - ((num_rows * (domino_height + domino_vert_spacing)) - domino_vert_spacing)) / 2
print(f"padding_height={padding_height}")

num_cols = int((args.width - args.dovetail_depth - domino_horiz_spacing) // (domino_width + domino_horiz_spacing))
print(f"num_cols={num_cols}")

padding_width = (args.width - args.dovetail_depth - (num_cols * (domino_width + domino_horiz_spacing))) / 2
print(f"padding_width={padding_width}")

# Adapted from https://github.com/augiev/Shaper-Dominos
dpi = 96
scale = dpi/25.4
fillet_rad = 2.5*scale
circle_rad = 1.25*scale
circle_grid = 5.08*scale
rect_w = domino_width*scale
rect_h = domino_height*scale

border_w = domino_horiz_spacing*scale
border_h = domino_vert_spacing*scale
xoff = rect_w/2 + padding_width*scale
yoff = rect_h/2 + padding_height*scale

def generate(d_outline, d_dots, rows, cols, previous=[]):
    vals = []
    while len(vals) < (rows*cols):
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
            vals.append(rand)


    row_col = []
    for r in range(rows):
        for c in range(cols):
            row_col.append((r,c))
    gen = zip(row_col, vals)

    for (r, c), spots in gen:
        xoff2 = xoff + c*(rect_w + border_w)
        yoff2 = yoff + r*(rect_h + border_h)

        geo_r = rows - r - 2
        if geo_r >= 0 and geo_r % 2 == 0:
            xoff2 += args.dovetail_depth*scale


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


previous = []

max_count = 903 # total number of valid fiducials (based on exhaustive search)

requested_count = num_rows*num_cols*args.num_plates
if requested_count > max_count:
    print(f'error, only {max_count} fiducials exist; requested {requested_count}')
    exit(1)

svg_dir = Path.cwd() / 'svgs'
if not svg_dir.is_dir():
    svg_dir.mkdir()

for i in range(args.num_plates):
    outpath_outline = svg_dir / f'{i}_outline.svg'
    outpath_dots = svg_dir / f'{i}_dots.svg'
    dwg_outline = Drawing(filename=str(outpath_outline), debug=True)
    dwg_dots = Drawing(filename=str(outpath_dots), debug=True)
    previous.extend(generate(dwg_outline, dwg_dots, num_rows, num_cols, previous))
    dwg_outline.save()
    dwg_dots.save()

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
        outfile = stl_dir / f"{i}-{layer}.stl"
        subprocess.run([
            OPENSCAD_EXE,
            "-o", outfile,
            "-D", f"width={args.width}",
            "-D", f"height={args.height}",
            "-D", f"thickness={args.thickness}",
            "-D", f"fid={i}",
            "-D", f"selector={lid}",
            "dovetail-shaperplates.scad"
        ], cwd=Path(__file__).parent)
