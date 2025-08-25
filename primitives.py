import math
from viz import VIZ_WIDTH_SCALE

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Line:
    def __init__(self, start: Point, end: Point, width: float):
        self.start = start
        self.end = end
        self.width = width

        self.length = self.calculate_length()

    def calculate_length(self):
        return math.hypot(self.end.x - self.start.x, self.end.y - self.start.y)

    def extend_to_intersection_with_y(self, y: float):
        # Extend the line to intersect with the given y-coordinate
        if self.start.y == self.end.y:
            # Line is horizontal
            return Line(Point(self.start.x, y), Point(self.end.x, y))
        else:
            
            slope = (self.end.y - self.start.y) / (self.end.x - self.start.x)
            x_intersect = (y - self.start.y) / slope + self.start.x
            return Line(Point(self.start.x, self.start.y), Point(x_intersect, y))

    def extend_to_intersection_with_x(self, x: float):
        # Extend the line to intersect with the given x-coordinate
        if self.start.x == self.end.x:
            # Line is vertical
            return Line(Point(x, self.start.y), Point(x, self.end.y), self.width)
        else:
            slope = (self.end.y - self.start.y) / (self.end.x - self.start.x)
            y_intersect = slope * (x - self.start.x) + self.start.y
            return Line(Point(self.start.x, self.start.y), Point(x, y_intersect), self.width)

    def draw(self, viz, color='blue', label="", width=0.1):
        viz.add_line(self.start, self.end, color=color, width=width*VIZ_WIDTH_SCALE, label=label)
    
    def get_start_end_metrics(self):
        return f"[Line] Start: ({self.start.x}, {self.start.y}) End: ({self.end.x}, {self.end.y})"

    def print_start_end_metrics(self):
        print(self.get_start_end_metrics())

    def __repr__(self):
        return self.get_start_end_metrics()

    def get_parameters_dict(self, offset_to: Point):

        return {
            "type": "gr_line",
            "start_x": self.start.x - offset_to.x,
            "start_y": -self.start.y - offset_to.y,
            "end_x": self.end.x - offset_to.x,
            "end_y": -self.end.y - offset_to.y,
            "width": self.width
        }

    def get_parameters(self):
        return str(self.get_parameters_dict)


class Arc:
    def __init__(self, center: Point, radius: float, start_angle: float, end_angle: float, width: float):
        self.center = center
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.width = width
    
    def get_start_point(self):
        # Calculate the start point of the arc
        start_x = self.center.x + self.radius * math.cos(self.start_angle)
        start_y = self.center.y + self.radius * math.sin(self.start_angle)
        return Point(start_x, start_y)

    def get_exit_point(self):
        # Calculate the exit point of the arc
        exit_x = self.center.x + self.radius * math.cos(self.end_angle)
        exit_y = self.center.y + self.radius * math.sin(self.end_angle)
        return Point(exit_x, exit_y)

    def get_tangent_angle_degrees_at_exit_point(self):
        # Tangent angle at the exit point in degrees
        tangent_angle = self.end_angle + math.pi / 2
        return math.degrees(tangent_angle)

    def get_tangent_line(self, length: float):
        # Get the tangent line at the exit point of the arc
        exit_point = self.get_exit_point()
        tangent_angle = self.get_tangent_angle_degrees_at_exit_point()
        # Calculate the end point of the tangent line
        end_x = exit_point.x + length * math.cos(math.radians(tangent_angle))
        end_y = exit_point.y + length * math.sin(math.radians(tangent_angle))
        return Line(exit_point, Point(end_x, end_y), self.width)

    def get_tangent_angle_degrees_at_starting_point(self):
        # Tangent angle at the starting point in degrees
        tangent_angle = self.start_angle - math.pi / 2
        return math.degrees(tangent_angle)

    def get_line_length(self):
        # Get the length of the arc in millimeters, used for precise trace length calculation
        # Formula: L = r * θ, e.g. 180 degree arc with r = 0.5: L = 0.5* π = 1.5708
        return self.radius * (self.end_angle - self.start_angle)

    def calculate_length(self):
        return self.get_line_length()

    def draw(self, viz, color='blue', label=None, width=0.1):
        viz.add_arc(self.center, self.radius, self.start_angle, self.end_angle, 
                   color=color, width=width*VIZ_WIDTH_SCALE, label=label)
    
    def print_center_start_angle_metrics(self):
        start_point = self.get_start_point()
        print(f"[Arc] Center: ({self.center.x}, {self.center.y}) Start: ({start_point.x}, {start_point.y}) Angle: {math.degrees(self.end_angle)} degrees")

    def get_start_mid_end_metrics(self):
        start_point = self.get_start_point()
        mid_point = Point(
            self.center.x + self.radius * math.cos((self.start_angle + self.end_angle) / 2),
            self.center.y + self.radius * math.sin((self.start_angle + self.end_angle) / 2)
        )
        end_point = self.get_exit_point()
        return f"[Arc] Start: ({start_point.x}, {start_point.y}) Mid: ({mid_point.x}, {mid_point.y}) End: ({end_point.x}, {end_point.y})"

    def print_start_mid_end_metrics(self):
        print(self.get_start_mid_end_metrics())

    def __repr__(self):
        return self.get_start_mid_end_metrics()

    def get_parameters_dict(self, offset_to: Point):
        start_point = self.get_start_point()
        end_point = self.get_exit_point()
        
        # Calculate the actual arc midpoint considering arc direction
        # Determine if arc is clockwise or counterclockwise
        angle_diff = self.end_angle - self.start_angle
        
        # Normalize angle difference to [-π, π]
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        # Calculate midpoint angle - use the actual arc path direction
        if angle_diff >= 0:  # counterclockwise arc
            mid_angle = self.start_angle + angle_diff / 2
        else:  # clockwise arc  
            mid_angle = self.start_angle + angle_diff / 2
        
        # Calculate midpoint on the arc
        mid_point = Point(
            self.center.x + self.radius * math.cos(mid_angle),
            self.center.y + self.radius * math.sin(mid_angle)
        )

        return {
            "type": "gr_arc",
            "start_x": start_point.x - offset_to.x,
            "start_y": -start_point.y - offset_to.y,
            "mid_x": mid_point.x - offset_to.x,
            "mid_y": -mid_point.y - offset_to.y,
            "end_x": end_point.x - offset_to.x,
            "end_y": -end_point.y - offset_to.y,
            "width": self.width
        }
