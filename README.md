# kicad-curved-diffpair-footprints
Python scripts for creating kicad footprints of diffpair segments featuring curves

## Installation
Create a virtual environment and install all required libraries
```bash
python -m venv venv
sudo chmod +x ./venv/bin/activate
pip install -r requirements.txt
```

## Example usage

```bash
python strafe.py 0 0 0.20 0.20 4.0 0.2 1.5708
Do you want to show a preview? (y/n) y # Opens diagram with rough visualization of the offset
Do you want to generate footprint file? (y/n) y 
Generated footprint: dp_strafe_right_w0.2_g0.2_offs4.0mm.kicad_mod
```

### Strafe
Curve resulting in an offsite to the side, while keeping the same heading. This type of curve is length-symmetrical i.e. does not cause skew in the diffpair.

Parameters:
Coordinate X, Coordinate Y - Right now these are a bit redundant, but I've kept them. Starting point of the diff pair, the point is in the middle of the pair, right between the traces.
Trace width - Your trace width. float, millimeters.
Trace gap - Your trace gap. float, millimeters.
Offset - Your desired offset. Positive is to the right.
Radius ratio - The ratio between curve radius and offset. Affects how aggressive the script will make the bends. Higher number = less aggressive.
Middle tangent angle - The angle between the middle tangent and the original X axis. Radians. The example above is at 90 degrees (orthagonal) to the X-axis.