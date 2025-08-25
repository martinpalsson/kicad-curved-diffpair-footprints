import math

import copy
from jinja2 import Template
from primitives import Point, Line, Arc
from viz import VIZ_WIDTH_SCALE, TraceVisualizer
import uuid

# Embedded Jinja template for Strafe footprint
STRAFE_FOOTPRINT_TEMPLATE = """(footprint "{{ footprint_name }}"
	(version {{ version | default("20241229") }})
	(generator "{{ generator | default("pcbnew") }}")
	(generator_version "{{ generator_version | default("9.0") }}")
	(layer "{{ layer | default("F.Cu") }}")
	(descr "{{ description }}")
	(property "Reference" "{{ reference | default("REF**") }}"
		(at {{ ref_pos_x | default(0.1) }} {{ ref_pos_y | default(1.6) }} {{ ref_rotation | default(0) }})
		(unlocked yes)
		(layer "{{ ref_layer | default("F.SilkS") }}")
		(uuid "{{ ref_uuid }}")
		(effects
			(font
				(size {{ ref_font_size | default(1) }} {{ ref_font_size | default(1) }})
				(thickness {{ ref_font_thickness | default(0.1) }})
			)
		)
	)
	(property "Value" "{{ value | default("Untitled") }}"
		(at {{ val_pos_x | default(0) }} {{ val_pos_y | default(1) }} {{ val_rotation | default(0) }})
		(unlocked yes)
		(layer "{{ val_layer | default("F.Fab") }}")
		(uuid "{{ val_uuid }}")
		(effects
			(font
				(size {{ val_font_size | default(1) }} {{ val_font_size | default(1) }})
				(thickness {{ val_font_thickness | default(0.15) }})
			)
		)
	)
	(property "Datasheet" "{{ datasheet | default("") }}"
		(at 0 0 0)
		(unlocked yes)
		(layer "F.Fab")
		(hide yes)
		(uuid "{{ datasheet_uuid }}")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(property "Description" "{{ footprint_name }}"
		(at 0 0 0)
		(unlocked yes)
		(layer "F.Fab")
		(hide yes)
		(uuid "{{ description_uuid }}")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(attr {{ attributes | default("exclude_from_pos_files exclude_from_bom") }})
{%- for line in fp_lines %}
	(fp_line
		(start {{ line.start_x }} {{ line.start_y }})
		(end {{ line.end_x }} {{ line.end_y }})
		(stroke
			(width {{ line.width }})
			(type {{ line.type | default("default") }})
		)
		(layer "{{ line.layer }}")
		(uuid "{{ line.uuid }}")
	)
{%- endfor %}
{%- for text in fp_texts %}
	(fp_text {{ text.text_type }} "{{ text.content }}"
		(at {{ text.pos_x }} {{ text.pos_y }} {{ text.rotation | default(0) }})
		(unlocked yes)
		(layer "{{ text.layer }}")
		(uuid "{{ text.uuid }}")
		(effects
			(font
				(size {{ text.font_size | default(1) }} {{ text.font_size | default(1) }})
				(thickness {{ text.font_thickness | default(0.15) }})
			)
		)
	)
{%- endfor %}
{%- for pad in pads %}
	(pad "{{ pad.number }}" smd {{ pad.shape }}
		(at {{ pad.pos_x }} {{ pad.pos_y }})
		(size {{ pad.size_x }} {{ pad.size_y }})
		(layers {{ pad.layers }})
		{%- if pad.shape == "custom" %}
		{%- if pad.die_length %}
		(die_length {{ pad.die_length }})
		{%- endif %}
		(options
			(clearance {{ pad.clearance | default("outline") }})
			(anchor {{ pad.anchor | default("circle") }})
		)
		(primitives
		{%- for primitive in pad.primitives %}
			{%- if primitive.type == "gr_arc" %}
			(gr_arc
				(start {{ primitive.start_x }} {{ primitive.start_y }})
				(mid {{ primitive.mid_x }} {{ primitive.mid_y }})
				(end {{ primitive.end_x }} {{ primitive.end_y }})
				(width {{ primitive.width }})
			)
			{%- elif primitive.type == "gr_line" %}
			(gr_line
				(start {{ primitive.start_x }} {{ primitive.start_y }})
				(end {{ primitive.end_x }} {{ primitive.end_y }})
				(width {{ primitive.width }})
			)
			{%- endif %}
		{%- endfor %}
		)
		{%- endif %}
		(uuid "{{ pad.uuid }}")
	)
{%- endfor %}
	(embedded_fonts no)
)"""

# Strafe class for generating curved diffpair offset.
# Parameters:
# - start: Starting point of the trace (x: float, y: float)
# - trace_width: Width of the trace (mm: float)
# - trace_gap: Gap between traces (mm: float)
# - offset_x: Offset in the x-direction (mm: float)
# - radius_scale: Scale factor for the radius, relative to offset_x. (ratio: float)
# - middle_tangent_angle: Angle (radians) of the middle tangent against original x-axis (rad: float)

class Strafe:
    def __init__(self, start: Point, trace_width: float, trace_gap: float, offset_x: float, radius_scale: float, middle_tangent_angle: float):
        self.start = start
        self.trace_width = trace_width
        self.trace_gap = trace_gap
        self.offset_x = offset_x
        self.radius_scale = radius_scale
        self.middle_tangent_angle = middle_tangent_angle

        self.minus_primitives = list()
        self.plus_primitives = list()

        self.offset_dir = False
        if self.offset_x >= 0:
            self.offset_dir = True

        self.plus_trace_length = 0.0
        self.minus_trace_length = 0.0

        self.calculate_trace()
        self.calculate_trace_length()
    

    def calculate_trace(self):

        self.minus_start_point = Point(self.start.x -(self.trace_width/2 + self.trace_gap/2), self.start.y)
        self.plus_start_point = Point(self.start.x + (self.trace_width/2 + self.trace_gap/2), self.start.y)

        trace_center_width = math.fabs(self.plus_start_point.x - self.minus_start_point.x)

        small_radius = math.fabs(self.offset_x * self.radius_scale)
        big_radius = small_radius + copy.deepcopy(trace_center_width)

        if self.offset_dir:
            first_bend_center = Point(self.plus_start_point.x + small_radius, self.plus_start_point.y)
            second_bend_center = Point(self.offset_x + (copy.deepcopy(trace_center_width) / 2) - copy.deepcopy(big_radius), math.fabs(self.offset_x * 2))

            # Order of primitives: [0: Arc1, 1: Arc2, 2: Line between Arc1 and Arc2]
            self.minus_primitives.append(Arc(copy.deepcopy(first_bend_center), big_radius, math.pi, -math.pi - self.middle_tangent_angle, self.trace_width))
            self.plus_primitives.append(Arc(copy.deepcopy(first_bend_center), small_radius, math.pi, -math.pi - self.middle_tangent_angle, self.trace_width))

            self.minus_primitives.append(Arc(copy.deepcopy(second_bend_center), small_radius, 0, -(2*math.pi) - self.middle_tangent_angle, self.trace_width))
            self.plus_primitives.append(Arc(copy.deepcopy(second_bend_center), big_radius, 0, -(2*math.pi) - self.middle_tangent_angle, self.trace_width))
        else:
            first_bend_center = Point(self.minus_start_point.x - small_radius, self.minus_start_point.y)
            second_bend_center = Point(self.offset_x - (copy.deepcopy(trace_center_width) / 2) + big_radius, math.fabs(self.offset_x * 2))

            # Order of primitives: [0: Arc1, 1: Arc2, 2: Line between Arc1 and Arc2]
            self.minus_primitives.append(Arc(copy.deepcopy(first_bend_center), small_radius, 0, self.middle_tangent_angle, self.trace_width))
            self.plus_primitives.append(Arc(copy.deepcopy(first_bend_center), big_radius, 0, self.middle_tangent_angle, self.trace_width))

            self.minus_primitives.append(Arc(copy.deepcopy(second_bend_center), big_radius, math.pi, math.pi + self.middle_tangent_angle, self.trace_width))
            self.plus_primitives.append(Arc(copy.deepcopy(second_bend_center), small_radius, math.pi, math.pi + self.middle_tangent_angle, self.trace_width))

        self.minus_primitives.append(self.minus_primitives[0].get_tangent_line(1))
        self.minus_primitives[-1] = self.minus_primitives[-1].extend_to_intersection_with_x(self.minus_primitives[1].get_exit_point().x)
        diff = self.minus_primitives[1].get_exit_point().y - self.minus_primitives[-1].end.y
        self.minus_primitives[1].center.y -= diff

        self.plus_primitives.append(self.plus_primitives[0].get_tangent_line(1))
        self.plus_primitives[-1] = self.plus_primitives[-1].extend_to_intersection_with_x(self.plus_primitives[1].get_exit_point().x)
        diff = self.plus_primitives[1].get_exit_point().y - self.plus_primitives[-1].end.y
        self.plus_primitives[1].center.y -= diff


        self.minus_end_point = self.minus_primitives[1].get_start_point()
        self.plus_end_point = self.plus_primitives[1].get_start_point()

    def calculate_trace_length(self):
        self.minus_trace_length = 0.0
        self.plus_trace_length = 0.0

        for primitive in self.minus_primitives:
            self.minus_trace_length += primitive.calculate_length()
        for primitive in self.plus_primitives:
            self.plus_trace_length += primitive.calculate_length()


    def print_metrics(self):
        for primitive in self.minus_primitives + self.plus_primitives:
            print(f"Primitive: {primitive}, Length: {primitive.calculate_length()}")

    def visualize(self):
        viz = TraceVisualizer()

        for primitive in self.minus_primitives:
            primitive.draw(viz, color='blue', width=self.trace_width*VIZ_WIDTH_SCALE)
        for primitive in self.plus_primitives:
            primitive.draw(viz, color='red', width=self.trace_width*VIZ_WIDTH_SCALE)

        viz.show()
    
    def get_general_direction(self):
        direction = "left"
        if self.offset_dir:
            direction = "right"
        
        return direction
    
    def generate_footprint_name(self):
        return f"dp_strafe_{self.get_general_direction()}_w{self.trace_width}_g{self.trace_gap}_offs{math.fabs(self.offset_x)}mm"
    
    def generate_footprint_description(self):
        return f"differential pair strafe/offset to the {self.get_general_direction()}, trae width: {self.trace_width} mm trace gap {self.trace_gap} mm offset {math.fabs(self.offset_x)} mm"

    def generate_footprint_parameters(self):
        minus_primitives = list()
        plus_primitives = list()

        for primitive in self.minus_primitives:
            minus_primitives.append(primitive.get_parameters_dict(self.minus_start_point))
        for primitive in self.plus_primitives:
            plus_primitives.append(primitive.get_parameters_dict(self.plus_start_point))

        parameters = {
                # Basic footprint info (same as before)
                "footprint_name": self.generate_footprint_name(),
                "description": self.generate_footprint_description(),

                # UUIDs (same as before)
                "ref_uuid": str(uuid.uuid4()),
                "val_uuid": str(uuid.uuid4()),
                "datasheet_uuid": str(uuid.uuid4()),
                "description_uuid": str(uuid.uuid4()),

                # Construction lines and text (same as before)
                "fp_texts": [
                    {
                        "text_type": "user",
                        "content": "${REFERENCE}",
                        "pos_x": 0,
                        "pos_y": 2.5,
                        "rotation": 0,
                        "layer": "F.Fab", 
                        "uuid": str(uuid.uuid4())
                    }
                ],
                
                # Pads - NOW WITH die_length
                "pads": [
                    # End pads (simple circles - no die_length)
                    {
                        "number": "1",
                        "shape": "circle",
                        "pos_x": self.minus_end_point.x,
                        "pos_y": -self.minus_end_point.y,
                        "size_x": self.trace_width,
                        "size_y": self.trace_width,
                        "layers": "F.Cu",
                        "uuid": str(uuid.uuid4())
                    },
                    {
                        "number": "2",
                        "shape": "circle",
                        "pos_x": self.plus_end_point.x,
                        "pos_y": -self.plus_end_point.y,
                        "size_x": self.trace_width,
                        "size_y": self.trace_width,
                        "layers": "F.Cu",
                        "uuid": str(uuid.uuid4())
                    },
                    
                    # Start pads (custom with trace path)
                    {
                        "number": "1", 
                        "shape": "custom",
                        "pos_x": self.minus_start_point.x,
                        "pos_y": -self.minus_start_point.y,
                        "size_x": self.trace_width,
                        "size_y": self.trace_width,
                        "layers": "F.Cu",
                        "die_length": self.minus_trace_length,
                        "clearance": "outline",
                        "anchor": "circle",
                        "primitives": minus_primitives,
                        "uuid": str(uuid.uuid4())
                    },
                    {
                        "number": "2", 
                        "shape": "custom",
                        "pos_x": self.plus_start_point.x,
                        "pos_y": -self.plus_start_point.y,
                        "size_x": self.trace_width,
                        "size_y": self.trace_width,
                        "layers": "F.Cu",
                        "die_length": self.plus_trace_length,
                        "clearance": "outline",
                        "anchor": "circle",
                        "primitives": plus_primitives,
                        "uuid": str(uuid.uuid4())
                    }
                ]
            }
        

        return parameters

    def generate_footprint_file(self, output_path: str=None):
        """
        Generate a KiCad footprint file from template and parameters
        
        Args:
            parameters (dict): All the footprint parameters as specified
            output_path (str, optional): Output file path. If None, uses footprint_name + '.kicad_mod'
            template_string (str, optional): Custom template string. If None, uses embedded template
        
        Returns:
            str: The rendered footprint content
        """

        parameters = self.generate_footprint_parameters()

        # Use embedded template by default
        template_content = STRAFE_FOOTPRINT_TEMPLATE
        
        # Create Jinja template and render
        template = Template(template_content)
        rendered_content = template.render(**parameters)
        
        # Determine output path
        if output_path is None:
            footprint_name = parameters.get('footprint_name', 'untitled_footprint')
            output_path = f"{footprint_name}.kicad_mod"
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        print(f"Generated footprint: {output_path}")
        return rendered_content

if __name__ == "__main__":

    import sys
    # Get command line arguments.
    # Coordinate X, Coordinate Y, trace width, trace gap, offset, radius scale, middle_tangent_angle --preview --generate
    if len(sys.argv) < 8:
        print("Usage: script.py <coord_x> <coord_y> <trace_width> <trace_gap> <offset> <radius_scale> <middle_tangent_angle> --preview --generate")
        sys.exit(1)

    coord_x = float(sys.argv[1])
    coord_y = float(sys.argv[2])
    trace_width = float(sys.argv[3])
    trace_gap = float(sys.argv[4])
    offset = float(sys.argv[5])
    radius_scale = float(sys.argv[6])
    middle_tangent_angle = float(sys.argv[7])
    preview = "--preview" in sys.argv
    generate = "--generate" in sys.argv

    bend = Strafe(Point(coord_x, coord_y), trace_width, trace_gap, offset, radius_scale, middle_tangent_angle)

    if generate:
        bend.generate_footprint_file()

    if preview:
        bend.visualize()

    exit(0)