num_rows = 2;
num_cols = 1;

// measured in inches
thickness = (1/16) * 25.4;
fid = "5c4d82d8";
selector = 1;
label = str("1/16\" - 4x6 - ", fid);

echo("Generating file ", fid);

dovetail_depth = 10;
dovetail_radius = 1;

domino_thickness = 0.4;
domino_width = 43;
domino_height = 12.7;
domino_spacing = 2.5;

dovetail_fit_tolerance = 0;

dovetail_angle = 60;

dovetail_width = domino_height + (2*dovetail_depth*tan(90-dovetail_angle));

grid_height = (domino_height + (dovetail_depth*tan(90-dovetail_angle))) * 2;

module dovetail(tolerance=0) { 
    let(tanlen = dovetail_radius * tan(90 - (dovetail_angle/2))) {
        difference() {
        union() {
            linear_extrude(thickness) {
                polygon(points = [
                    [tolerance, dovetail_width - dovetail_depth*tan(90-dovetail_angle) + tanlen],
                    [
                        tanlen * cos(90 - dovetail_angle) - (tolerance * cos(dovetail_angle)),
                        dovetail_width - dovetail_depth*tan(90-dovetail_angle) + (tanlen * sin(90 - dovetail_angle)) + (tolerance * sin(dovetail_angle))],
                    [
                        dovetail_depth - (tanlen * cos(90 - dovetail_angle)) - (tolerance * cos(dovetail_angle)),
                        dovetail_width - (tanlen * sin(90 - dovetail_angle)) + (tolerance * sin(dovetail_angle))
                    ],
                    [dovetail_depth + tolerance, dovetail_width - tanlen],
                    [dovetail_depth + tolerance, tanlen],
                    [
                        dovetail_depth - (tanlen * cos(90 - dovetail_angle)) - (tolerance * cos(dovetail_angle)),
                        tanlen * sin(90 - dovetail_angle) - (tolerance * sin(dovetail_angle))
                    ],
                    [
                        tanlen * cos(90 - dovetail_angle) - (tolerance * cos(dovetail_angle)),
                        dovetail_depth*tan(90-dovetail_angle) - (tanlen * sin(90 - dovetail_angle)) - (tolerance * sin(dovetail_angle))
                    ],
                    [tolerance, dovetail_depth*tan(90-dovetail_angle) - tanlen]
                ]);
            }
            
            translate([dovetail_depth - dovetail_radius, dovetail_width - tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius + tolerance, center=false, $fn=60);
            translate([dovetail_depth - dovetail_radius, tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius + tolerance, center=false, $fn=60);
        };
        translate([dovetail_radius, dovetail_width - dovetail_depth*tan(90-dovetail_angle) + tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius - tolerance, center=false, $fn=60);
            translate([dovetail_radius, dovetail_depth*tan(90-dovetail_angle) - tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius - tolerance, center=false, $fn=60);
        }
    }
}

module dominos(fid) {
    translate([0, grid_height * num_rows, 0])
    linear_extrude(domino_thickness)
    scale(25.4/96)
    difference() {
        import(str("svgs/", num_rows, "_", num_cols, "_", fid, "_outline.svg"));
        import(str("svgs/", num_rows, "_", num_cols, "_", fid, "_dots.svg"));
    }
}

module label() {
    if (num_cols >= 3)
    translate([num_cols * (domino_width + domino_spacing) - 2, num_rows * (domino_height + dovetail_depth*2) - dovetail_depth + 1.5, domino_thickness])
    rotate([180, 0, 180])
    linear_extrude(domino_thickness)
    text(label, size=7, font="Segoe UI Black");
}

if(selector)
color("white")
difference() {
union() {
    cube([(domino_width + domino_spacing) * num_cols, grid_height * num_rows, thickness]);
    
    for(i = [0:1:num_rows-1])
    translate([(domino_width + domino_spacing)*num_cols, (dovetail_width/2) - dovetail_depth*tan(90-dovetail_angle) + (i*grid_height), 0])
    dovetail();
    
    for(i = [0:1:num_cols-1])
    translate([dovetail_width + (dovetail_depth - dovetail_width + domino_width+domino_spacing)/2 + i*(domino_width + domino_spacing), num_rows*grid_height, 0])
    rotate([0, 0, 90])
    dovetail();
}

for(i = [0:1:num_rows-1])
translate([0, (dovetail_width/2) - dovetail_depth*tan(90-dovetail_angle) + (i*grid_height), 0])
dovetail(dovetail_fit_tolerance);

for(i = [0:1:num_cols-1])
translate([dovetail_width + (dovetail_depth - dovetail_width + domino_width+domino_spacing)/2 + i*(domino_width + domino_spacing), 0, 0])
rotate([0, 0, 90])
dovetail(dovetail_fit_tolerance);

#dominos(fid);
#label();
}
else
color("black")
union() {
dominos(fid);
label();
}
