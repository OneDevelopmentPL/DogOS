# Small Ball Tracking on Raspberry Pi 4B

High-performance real-time small ball tracking optimized for the Raspberry Pi 4B (4GB). It uses a threaded video stream capture to avoid camera I/O bottlenecking and processed with OpenCV using optimized HSV masking and contour checking.

This setup achieves stable 30+ FPS (or the maximum physical limit of the camera sensor) on Raspberry Pi 4B.

## Installation Requirements

On your Raspberry Pi, install the required system libraries and dependencies:

```bash
# Update package lists
sudo apt-get update

# Install OpenCV dependencies
sudo apt-get install -y libhdf5-dev libhdf5-serial-dev libhdf5-103
优质 # (Raspberry Pi OS packages might differ slightly, but standard OpenCV install works)
sudo apt-get install -y libqtgui4 libqt5gui5 libqt4-test libjasper-dev

# Install Python requirements
pip3 install opencv-python numpy
```

## How to Run

### 1. Calibration Mode (Highly Recommended first step)
To tune the tracker to your specific ball's color (e.g. green, orange, yellow):
```bash
python3 ball_tracker.py --calibrate
```
- Sliders/Trackbars will open allowing you to adjust minimum/maximum Hue, Saturation, and Value (HSV).
- Adjust the sliders until only the ball is visible as white in the `Mask` window and has a tracking circle drawn around it in the `Feed` window.
- Press **`s`** on your keyboard to save these values into `config.json`.
- Press **`q`** to quit.

### 2. Normal Mode
Once calibrated, run:
```bash
python3 ball_tracker.py
```

### 3. Headless Mode (Maximum Performance)
For headless systems (e.g., if you run the script over SSH without GUI redirection):
```bash
python3 ball_tracker.py --headless
```
This disables UI display functions (`cv2.imshow`), which saves significant CPU cycles and improves processing speed.

## Performance Tuning on Raspberry Pi 4B
- **Resolution**: Lower resolutions (like `640x480` or `320x240`) are processed much faster. You can change this in `config.json`.
- **Camera Index**: If you use a Picamera (legacy V4L2 drivers) or a USB camera, make sure `camera_index` in `config.json` points to the correct camera device (usually `0` or `1`).
- **Threads**: The `ThreadedVideoStream` class separates frame capture from image processing. This prevents the Pi's CPU cores from idling while waiting for the next camera frame.
