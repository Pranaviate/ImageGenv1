#!/Users/pranav.sharma/Documents/MLprojects/explore-etoro-signals/.conda/env/bin/python

import os
from PIL import Image
import argparse

# Supported image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def is_valid_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

# === Custom Overlay Area Configuration ===
# Define margins as percentages of the base image dimensions.
# For the X axis (horizontal):
X_LEFT_MARGIN_PERCENT = 10   # Margin from left (if INVERT_X is False) or from right (if True)
X_RIGHT_MARGIN_PERCENT = 30  # Margin from right (if INVERT_X is False) or from left (if True)
# For the Y axis (vertical):
Y_TOP_MARGIN_PERCENT = 10    # Margin from top (if INVERT_Y is False) or from bottom (if True)
Y_BOTTOM_MARGIN_PERCENT = 10 # Margin from bottom (if INVERT_Y is False) or from top (if True)

# Inversion flags:
# If INVERT_X is True, the percentages for X will be interpreted from the opposite sides.
# Similarly for INVERT_Y.
INVERT_X = False
INVERT_Y = False
# ===========================================

def parse_scales(scales_str, expected_count):
    """
    Parse a comma-separated list of scaling percentages.
    Scaling values above 100 indicate a zoom-in (e.g., 150 means 150% of original size).
    Returns a list of multipliers (e.g., 150 becomes 1.5).
    """
    scales = [s.strip() for s in scales_str.split(",")]
    if len(scales) != expected_count:
        raise ValueError(f"Expected {expected_count} scale value(s) but got {len(scales)}.")
    try:
        # Convert percentages to multipliers (i.e., 150 becomes 1.5)
        scales = [float(s) / 100.0 for s in scales]
    except ValueError:
        raise ValueError("Scaling percentages must be numbers.")
    return scales

def main():
    parser = argparse.ArgumentParser(
        description="Overlay images on a base image within a custom-defined area. "
                    "Optionally specify scaling percentages for each overlay image (values > 100 zoom in)."
    )
    parser.add_argument("base_image", help="Path to the base image (jpg, jpeg, or png)")
    parser.add_argument("overlay_images", nargs="+", help="Paths to overlay images (jpg, jpeg, or png) in order")
    parser.add_argument("--output", "-o", default="output.png", help="Output file name (default: output.png)")
    parser.add_argument("--scales", "-s", default=None,
                        help="Comma-separated list of scaling percentages for each overlay image (e.g., '150,50,100'). "
                             "Each value scales the corresponding overlay relative to its original size; values above 100 zoom in.")
    args = parser.parse_args()

    # Validate image formats
    if not is_valid_image(args.base_image):
        print("Error: Base image file is not a supported format (jpg, jpeg, png).")
        return
    for overlay in args.overlay_images:
        if not is_valid_image(overlay):
            print(f"Error: Overlay image '{overlay}' is not a supported format (jpg, jpeg, png).")
            return

    # Parse scaling percentages if provided
    manual_scales = None
    if args.scales:
        try:
            manual_scales = parse_scales(args.scales, len(args.overlay_images))
        except ValueError as e:
            print(f"Error parsing scales: {e}")
            return

    # Open base image and convert to RGBA for transparency support
    base_img = Image.open(args.base_image).convert("RGBA")
    base_width, base_height = base_img.size

    # Compute overlay area boundaries based on custom parameters
    if not INVERT_X:
        overlay_x_start = base_width * (X_LEFT_MARGIN_PERCENT / 100)
        overlay_x_end = base_width - base_width * (X_RIGHT_MARGIN_PERCENT / 100)
    else:
        overlay_x_start = base_width * (X_RIGHT_MARGIN_PERCENT / 100)
        overlay_x_end = base_width - base_width * (X_LEFT_MARGIN_PERCENT / 100)

    if not INVERT_Y:
        overlay_y_start = base_height * (Y_TOP_MARGIN_PERCENT / 100)
        overlay_y_end = base_height - base_height * (Y_BOTTOM_MARGIN_PERCENT / 100)
    else:
        overlay_y_start = base_height * (Y_BOTTOM_MARGIN_PERCENT / 100)
        overlay_y_end = base_height - base_height * (Y_TOP_MARGIN_PERCENT / 100)

    overlay_area_width = overlay_x_end - overlay_x_start
    overlay_area_height = overlay_y_end - overlay_y_start

    # Calculate allowed width per overlay if arranging them horizontally in the overlay area
    n = len(args.overlay_images)
    allowed_width = overlay_area_width / n

    # Set starting x coordinate based on inversion flag.
    if not INVERT_X:
        current_x = overlay_x_start
    else:
        current_x = overlay_x_end - allowed_width

    # Create composite image as a copy of the base image
    composite = base_img.copy()

    # Process each overlay image
    for i, overlay_path in enumerate(args.overlay_images):
        overlay = Image.open(overlay_path).convert("RGBA")
        original_w, original_h = overlay.size

        # Apply manual scaling if provided; otherwise, use automatic scaling to fit allowed area.
        if manual_scales:
            # Scale overlay relative to its original size (values > 100 zoom in)
            scale_multiplier = manual_scales[i]
            new_w = int(original_w * scale_multiplier)
            new_h = int(original_h * scale_multiplier)
        else:
            new_w, new_h = original_w, original_h

        # Ensure the (possibly zoomed) overlay fits within its allocated slot;
        # compute an additional scaling factor if needed (but do not upscale further if it already fits).
        additional_scale = min(allowed_width / new_w, overlay_area_height / new_h, 1.0)
        final_w = int(new_w * additional_scale)
        final_h = int(new_h * additional_scale)

        overlay_resized = overlay.resize((final_w, final_h), resample=Image.LANCZOS)

        # Center the overlay within its allotted slot in the overlay area.
        pos_x = current_x + (allowed_width - final_w) / 2
        pos_y = overlay_y_start + (overlay_area_height - final_h) / 2

        composite.paste(overlay_resized, (int(pos_x), int(pos_y)), overlay_resized)

        # Update current_x based on inversion flag.
        if not INVERT_X:
            current_x += allowed_width
        else:
            current_x -= allowed_width

    composite.save(args.output)
    print(f"Saved composite image to {args.output}")

if __name__ == "__main__":
    main()


# python image_gen.py image_files/base.jpg image_files/cpp-logo.png image_files/saa-logo.png --output image_files/composite.png --scales "100,100"