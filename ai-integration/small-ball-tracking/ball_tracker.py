#!/usr/bin/env python3
import cv2
import numpy as np
import time
import json
import os
import argparse
from threading import Thread

class ThreadedVideoStream:
    """
    Spawns a separate thread to continuously grab frames from the camera.
    This significantly improves FPS on Raspberry Pi by removing I/O blocking from the main loop.
    """
    def __init__(self, src=0, width=640, height=480):
        self.stream = cv2.VideoCapture(src)
        if not self.stream.isOpened():
            raise IOError(f"Could not open video source {src}")
            
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Read the first frame
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while not self.stopped:
            (self.grabbed, frame) = self.stream.read()
            if not self.grabbed:
                # If we lose connection or fail to read, sleep briefly to avoid 100% CPU spinning
                time.sleep(0.01)
                continue
            self.frame = frame

    def read(self):
        return self.frame if self.grabbed else None

    def stop(self):
        self.stopped = True
        self.stream.release()

class BallTracker:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.load_config()
        self.vs = None

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config.json, using defaults: {e}")
                self.set_default_config()
        else:
            self.set_default_config()
            self.save_config()

    def set_default_config(self):
        self.config = {
            "camera_index": 0,
            "resolution": {"width": 640, "height": 480},
            "hsv_thresholds": {
                "h_min": 0, "s_min": 0, "v_min": 180,
                "h_max": 179, "s_max": 60, "v_max": 255
            },
            "detection_settings": {
                "min_radius": 5,
                "max_radius": 250,
                "min_circularity": 0.2
            },
            "show_preview": True,
            "verbose": True
        }

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def track(self, calibration_mode=False):
        cam_idx = self.config["camera_index"]
        width = self.config["resolution"]["width"]
        height = self.config["resolution"]["height"]

        print(f"Starting video stream on camera {cam_idx} with resolution {width}x{height}...")
        try:
            self.vs = ThreadedVideoStream(src=cam_idx, width=width, height=height).start()
        except IOError as e:
            print(f"\n[ERROR] Camera initialization failed: {e}")
            print("Please check if:")
            print(" 1. The camera is physically connected.")
            print(" 2. The 'camera_index' in config.json is correct.")
            print(" 3. (On macOS) Your terminal emulator has permission to access the Camera (System Settings -> Privacy & Security -> Camera).")
            return

        print("Waiting for camera sensor to warm up...")
        # Check if we successfully retrieve a frame within 3 seconds
        warmup_start = time.time()
        frame_ready = False
        while time.time() - warmup_start < 3.0:
            if self.vs.read() is not None:
                frame_ready = True
                break
            time.sleep(0.1)

        if not frame_ready:
            print("\n[ERROR] Unable to retrieve frames from the camera.")
            print("Please verify the camera is functioning and permission is granted.")
            self.vs.stop()
            return

        hsv_t = self.config["hsv_thresholds"]
        det_s = self.config["detection_settings"]
        show_preview = self.config["show_preview"] or calibration_mode

        if calibration_mode:
            print("Calibration Mode Enabled. Use the trackbars to adjust HSV thresholds.")
            print("--> IMPORTANT: You MUST click/focus on the video window ('Ball Tracker - Feed') for keyboard keys ('s' to save, 'q' to quit) to work!")
            cv2.namedWindow("Trackbars", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Trackbars", 500, 300)
            cv2.createTrackbar("H Min", "Trackbars", hsv_t["h_min"], 179, lambda x: None)
            cv2.createTrackbar("H Max", "Trackbars", hsv_t["h_max"], 179, lambda x: None)
            cv2.createTrackbar("S Min", "Trackbars", hsv_t["s_min"], 255, lambda x: None)
            cv2.createTrackbar("S Max", "Trackbars", hsv_t["s_max"], 255, lambda x: None)
            cv2.createTrackbar("V Min", "Trackbars", hsv_t["v_min"], 255, lambda x: None)
            cv2.createTrackbar("V Max", "Trackbars", hsv_t["v_max"], 255, lambda x: None)

        fps_start_time = time.time()
        fps_counter = 0
        fps = 0.0

        try:
            consecutive_failures = 0
            while True:
                frame = self.vs.read()
                if frame is None:
                    consecutive_failures += 1
                    if consecutive_failures > 100:
                        print("\n[ERROR] Lost connection to camera stream.")
                        break
                    time.sleep(0.01)
                    continue
                consecutive_failures = 0

                # RPi performance optimization: optional blur/downscale if frame is large,
                # but since we default to 640x480 or lower, a simple Gaussian Blur is enough.
                blurred = cv2.GaussianBlur(frame, (11, 11), 0)
                hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

                # Get dynamic values if in calibration mode
                if calibration_mode:
                    h_min = cv2.getTrackbarPos("H Min", "Trackbars")
                    h_max = cv2.getTrackbarPos("H Max", "Trackbars")
                    s_min = cv2.getTrackbarPos("S Min", "Trackbars")
                    s_max = cv2.getTrackbarPos("S Max", "Trackbars")
                    v_min = cv2.getTrackbarPos("V Min", "Trackbars")
                    v_max = cv2.getTrackbarPos("V Max", "Trackbars")
                else:
                    h_min, h_max = hsv_t["h_min"], hsv_t["h_max"]
                    s_min, s_max = hsv_t["s_min"], hsv_t["s_max"]
                    v_min, v_max = hsv_t["v_min"], hsv_t["v_max"]

                lower_hsv = np.array([h_min, s_min, v_min])
                upper_hsv = np.array([h_max, s_max, v_max])

                # Create mask and clean up noise (dilation/erosion)
                mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)

                # Find contours in the mask
                contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                center = None
                radius = 0

                if len(contours) > 0:
                    # Filter contours based on circularity and radius size to avoid noise
                    valid_contours = []
                    for c in contours:
                        ((x, y), r) = cv2.minEnclosingCircle(c)
                        # Check size
                        if det_s["min_radius"] <= r <= det_s["max_radius"]:
                            _, _, w_b, h_b = cv2.boundingRect(c)
                            aspect_ratio = float(w_b) / h_b if h_b > 0 else 0
                            
                            # Very loose aspect ratio check (ignores extremely long fluorescent lights or table edges)
                            if 0.4 <= aspect_ratio <= 2.5:
                                area = cv2.contourArea(c)
                                circle_area = np.pi * (r ** 2)
                                circularity = area / circle_area if circle_area > 0 else 0
                                
                                # Check if it's somewhat round (rejects completely square furniture and jagged walls)
                                if circularity >= det_s["min_circularity"]:
                                    valid_contours.append((c, r, (int(x), int(y))))

                    if len(valid_contours) > 0:
                        # Get the largest valid contour
                        largest_contour = max(valid_contours, key=lambda x: x[1])
                        c, radius, center = largest_contour

                        # Output coordinate of the tracked ball
                        if self.config["verbose"]:
                            print(f"Ball detected at X: {center[0]}, Y: {center[1]}, Radius: {radius:.1f} | FPS: {fps:.1f}")

                        # Draw indicator on frame
                        if show_preview:
                            x_rect, y_rect, w_rect, h_rect = cv2.boundingRect(c)
                            cv2.rectangle(frame, (x_rect, y_rect), (x_rect + w_rect, y_rect + h_rect), (0, 255, 255), 2)
                            cv2.circle(frame, center, 5, (0, 0, 255), -1)

                # Calculate FPS
                fps_counter += 1
                if (time.time() - fps_start_time) > 1.0:
                    fps = fps_counter / (time.time() - fps_start_time)
                    fps_counter = 0
                    fps_start_time = time.time()

                if show_preview:
                    # Draw FPS
                    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.imshow("Ball Tracker - Feed", frame)
                    try:
                        cv2.setWindowProperty("Ball Tracker - Feed", cv2.WND_PROP_TOPMOST, 1)
                    except:
                        pass
                    if calibration_mode:
                        cv2.imshow("Ball Tracker - Mask", mask)
                        try:
                            cv2.setWindowProperty("Ball Tracker - Mask", cv2.WND_PROP_TOPMOST, 1)
                        except:
                            pass

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("s") and calibration_mode:
                    # Save current calibration values
                    self.config["hsv_thresholds"] = {
                        "h_min": h_min, "s_min": s_min, "v_min": v_min,
                        "h_max": h_max, "s_max": s_max, "v_max": v_max
                    }
                    self.save_config()
                    print("Calibration parameters saved successfully to config.json!")

        finally:
            if self.vs:
                self.vs.stop()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="High performance small ball tracker for Raspberry Pi")
    parser.add_argument("--calibrate", action="store_true", help="Start in calibration mode with HSV trackbars")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json")
    parser.add_argument("--headless", action="store_true", help="Run without UI preview (best performance)")
    
    args = parser.parse_args()
    
    tracker = BallTracker(config_path=args.config)
    if args.headless:
        tracker.config["show_preview"] = False
        
    tracker.track(calibration_mode=args.calibrate)
