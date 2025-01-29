// ALL MEASUREMENTS IN mm
width = 260;
height = 210;
thickness = (1/16) * 25.4;

dovetail_depth = 15;
dovetail_radius = 1;
domino_thickness = 0.4;

domino_width = 43;
domino_height = 12.7;
domino_spacing = 5;

dovetail_fit_tolerance = 0.25;

dovetail_angle = max(
    60,
    atan(dovetail_depth / domino_spacing)
);

num_rows = floor((height - (dovetail_depth*2) + domino_spacing) / (domino_height + domino_spacing));
echo(num_rows);


padding_height = (height - (dovetail_depth*2) - ((num_rows * (domino_height + domino_spacing)) - domino_spacing)) / 2;
echo(padding_height);

dovetail_width = domino_height + (domino_spacing * 2);

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
    translate([0, height - dovetail_depth, thickness-domino_thickness])
    linear_extrude(domino_thickness)
    scale(25.4/96)
    difference() {
        import(str(fid, "_outline.svg"));
        import(str(fid, "_dots.svg"));
    }
}

difference() {
    union() {
        cube([width - dovetail_depth, height - dovetail_depth, thickness], false);
        for (i = [0 : 2 : num_rows-3] )
            translate([width - dovetail_depth, i*(domino_spacing + domino_height) + domino_height + dovetail_depth + padding_height, 0])
            dovetail(-dovetail_fit_tolerance);
        for (i = [0 : 2 : floor((width - (dovetail_depth*2)) / dovetail_width)-1])
            translate([dovetail_width * (i+1) + dovetail_depth, height - dovetail_depth, 0])
            rotate([0, 0, 90])
            dovetail(-dovetail_fit_tolerance);
    }
    for (i = [0 : 2 : num_rows-3] )
        translate([0, i*(domino_spacing + domino_height) + domino_height + dovetail_depth + padding_height, 0]) dovetail();
    
    for (i = [0 : 2 : floor((width - (dovetail_depth*2)) / dovetail_width)-1])
        translate([dovetail_width * (i+1) + dovetail_depth, 0, 0]) rotate([0, 0, 90]) dovetail();
    #dominos(1);
}
     
