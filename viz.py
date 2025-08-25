import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc
import math

VIZ_WIDTH_SCALE = 10

class TraceVisualizer:
    def __init__(self, figsize=(12, 8)):
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        
    def add_line(self, start, end, color='blue', width=2, label=None):
        """Add a straight line from start to end"""
        x_vals = [start.x, end.x]
        y_vals = [start.y, end.y]
        self.ax.plot(x_vals, y_vals, color=color, linewidth=width, label=label)

    def add_arc(self, center, radius, start_angle_rad, end_angle_rad, color='blue', width=2, label=None):
        """Add an arc. Angles in radians, 0° = positive x-axis"""
        # Create arc points
        start_rad = start_angle_rad
        end_rad = end_angle_rad

        # Handle angle wrapping
        if end_rad < start_rad:
            end_rad += 2 * math.pi
            
        angles = np.linspace(start_rad, end_rad, 100)
        x_points = center.x + radius * np.cos(angles)
        y_points = center.y + radius * np.sin(angles)

        self.ax.plot(x_points, y_points, color=color, linewidth=width, label=label)
        
    def add_point(self, point, color='red', size=50, label=None):
        """Add a point marker"""
        self.ax.scatter(point.x, point.y, c=color, s=size, label=label, zorder=5)

    def add_text(self, point, text, fontsize=10):
        """Add text annotation"""
        self.ax.annotate(text, (point.x, point.y), fontsize=fontsize)

    def set_limits(self, xlim=None, ylim=None):
        """Set axis limits"""
        if xlim:
            self.ax.set_xlim(xlim)
        if ylim:
            self.ax.set_ylim(ylim)
            
    def show(self, title="Trace Route"):
        """Display the plot"""
        self.ax.set_title(title)
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        if self.ax.get_legend_handles_labels()[0]:  # Check if there are labels
            self.ax.legend()
        plt.show()
        
    def save(self, filename, title="Trace Route"):
        """Save to file"""
        self.ax.set_title(title)
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        if self.ax.get_legend_handles_labels()[0]:
            self.ax.legend()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved to {filename}")