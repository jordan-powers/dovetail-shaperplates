num_rows = 1;
num_cols = 3;

// measured in inches
thickness = (1/16) * 25.4;
fid = "0000";
selector = 1;
label = str("1/16\" - ",num_rows,"x",num_cols," - ", fid);

echo("Generating file ", fid);

dovetail_depth = (5/16) * 25.4;
dovetail_radius = (1/16) * 25.4;

domino_thickness = 0.4;
domino_width = 43;
domino_height = 12.7;
domino_spacing = 2.5;

dovetail_fit_tolerance = -0.05;

dovetail_angle = 60;

dovetail_width = domino_height + (2*dovetail_depth*tan(90-dovetail_angle));

grid_height = (domino_height + (dovetail_depth*tan(90-dovetail_angle))) * 2;

module dovetail(width=dovetail_width, tolerance=0) { 
    let(tanlen = dovetail_radius * tan(90 - (dovetail_angle/2))) {
        difference() {
        union() {
            linear_extrude(thickness) {
                polygon(points = [
                    [tolerance, width - dovetail_depth*tan(90-dovetail_angle) + tanlen],
                    [
                        tanlen * cos(90 - dovetail_angle) - (tolerance * cos(dovetail_angle)),
                        width - dovetail_depth*tan(90-dovetail_angle) + (tanlen * sin(90 - dovetail_angle)) + (tolerance * sin(dovetail_angle))],
                    [
                        dovetail_depth - (tanlen * cos(90 - dovetail_angle)) - (tolerance * cos(dovetail_angle)),
                        width - (tanlen * sin(90 - dovetail_angle)) + (tolerance * sin(dovetail_angle))
                    ],
                    [dovetail_depth + tolerance, width - tanlen],
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
            
            translate([dovetail_depth - dovetail_radius, width - tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius + tolerance, center=false, $fn=60);
            translate([dovetail_depth - dovetail_radius, tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius + tolerance, center=false, $fn=60);
        };
        translate([dovetail_radius, width - dovetail_depth*tan(90-dovetail_angle) + tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius - tolerance, center=false, $fn=60);
            translate([dovetail_radius, dovetail_depth*tan(90-dovetail_angle) - tanlen, 0])
            cylinder(h=thickness, r=dovetail_radius - tolerance, center=false, $fn=60);
        }
    }
}

module dominos(fid) {
    translate([num_cols * (domino_width + domino_spacing) + dovetail_depth, grid_height * num_rows, domino_thickness])
    rotate([180, 0, 180])
    linear_extrude(domino_thickness)
    scale(25.4/96)
    difference() {
        import(str("svgs/", num_rows, "_", num_cols, "_", fid, "_outline.svg"));
        import(str("svgs/", num_rows, "_", num_cols, "_", fid, "_dots.svg"));
    }
}

module label() {
    if (num_cols >= 3)
    translate([num_cols * (domino_width + domino_spacing) - 2, num_rows * grid_height - dovetail_depth - 1, domino_thickness])
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
    translate([(domino_width + domino_spacing)*3/4 + dovetail_depth*tan(90-dovetail_angle)/2 + i*(domino_width + domino_spacing), num_rows*grid_height, 0])
    rotate([0, 0, 90])
    dovetail(width=((domino_width + domino_spacing)/2 + dovetail_depth*tan(90-dovetail_angle)));
}

for(i = [0:1:num_rows-1])
translate([0, (dovetail_width/2) - dovetail_depth*tan(90-dovetail_angle) + (i*grid_height), 0])
dovetail(tolerance=dovetail_fit_tolerance);

for(i = [0:1:num_cols-1])
translate([(domino_width + domino_spacing)*3/4 + dovetail_depth*tan(90-dovetail_angle)/2 + i*(domino_width + domino_spacing), 0, 0])
rotate([0, 0, 90])
dovetail(width=((domino_width + domino_spacing)/2 + dovetail_depth*tan(90-dovetail_angle)), tolerance=dovetail_fit_tolerance);

#dominos(fid);
#label();
}
else
color("black")
union() {
dominos(fid);
label();
}
