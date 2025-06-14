import pyautogui
import keyboard
import time
import cv2
import numpy as np
from threading import Thread, Lock

# ======================
# CONFIGURATION SETTINGS
# ======================
ANTI_RECOIL_TOGGLE_KEY = 'f1'
AIMBOT_TOGGLE_KEY = 'f2'
SHOOT_KEY = 'ctrl'  # Key used for shooting in-game
ENEMY_COLOR = (0, 0, 255)  # BGR color to detect (red in this example)
COLOR_TOLERANCE = 50  # Color detection sensitivity
SCAN_RADIUS = 300  # Pixels around crosshair to search for enemies
ANTI_RECOIL_STRENGTH = 0.5  # Recoil correction speed (0-1)

# ======================
# GLOBAL STATE
# ======================
anti_recoil_active = False
aimbot_active = False
shooting = False
last_mouse_position = pyautogui.position()
program_running = True
data_lock = Lock()

# ======================
# ANTI-RECOIL SYSTEM
# ======================
def anti_recoil_controller():
    global shooting, last_mouse_position
    
    while program_running:
        if anti_recoil_active and shooting:
            with data_lock:
                current_position = pyautogui.position()
                
                # Detect recoil (unintended cursor movement)
                if current_position != last_mouse_position:
                    screen_center = (pyautogui.size().width // 2, 
                                    pyautogui.size().height // 2)
                    
                    # Calculate correction vector
                    dx = screen_center[0] - current_position[0]
                    dy = screen_center[1] - current_position[1]
                    
                    # Apply smoothed correction
                    new_x = current_position[0] + dx * ANTI_RECOIL_STRENGTH
                    new_y = current_position[1] + dy * ANTI_RECOIL_STRENGTH
                    
                    pyautogui.moveTo(new_x, new_y, _pause=False)
                    last_mouse_position = (new_x, new_y)
        
        time.sleep(0.01)  # 10ms update rate

# ======================
# AIMBOT SYSTEM
# ======================
def find_enemy_position():
    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width // 2, screen_height // 2
    
    # Define search area around crosshair
    scan_area = (
        max(0, center_x - SCAN_RADIUS),
        max(0, center_y - SCAN_RADIUS),
        min(screen_width, center_x + SCAN_RADIUS),
        min(screen_height, center_y + SCAN_RADIUS)
    )
    
    # Capture screen region
    screenshot = pyautogui.screenshot(region=scan_area)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Create color mask
    lower_bound = np.array([
        max(0, ENEMY_COLOR[0] - COLOR_TOLERANCE),
        max(0, ENEMY_COLOR[1] - COLOR_TOLERANCE),
        max(0, ENEMY_COLOR[2] - COLOR_TOLERANCE)
    ])
    upper_bound = np.array([
        min(255, ENEMY_COLOR[0] + COLOR_TOLERANCE),
        min(255, ENEMY_COLOR[1] + COLOR_TOLERANCE),
        min(255, ENEMY_COLOR[2] + COLOR_TOLERANCE)
    ])
    
    mask = cv2.inRange(frame, lower_bound, upper_bound)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Find largest contour
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    largest_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest_contour) < 100:  # Minimum size threshold
        return None
    
    # Calculate enemy center
    moments = cv2.moments(largest_contour)
    enemy_x = int(moments["m10"] / moments["m00"]) + scan_area[0]
    enemy_y = int(moments["m01"] / moments["m00"]) + scan_area[1]
    
    return (enemy_x, enemy_y)

def aimbot_controller():
    last_detection_time = 0
    
    while program_running:
        if aimbot_active:
            current_time = time.time()
            
            # Reduce CPU usage when no enemies detected
            if current_time - last_detection_time > 2.0:  # 2-second cooldown
                time.sleep(0.1)
                continue
            
            enemy_pos = find_enemy_position()
            if enemy_pos:
                last_detection_time = current_time
                pyautogui.moveTo(enemy_pos[0], enemy_pos[1], 0.15, _pause=False)
        else:
            time.sleep(0.1)

# ======================
# INPUT HANDLING
# ======================
def monitor_inputs():
    global shooting, anti_recoil_active, aimbot_active, last_mouse_position
    
    while program_running:
        # Update mouse position when not shooting
        if not shooting:
            with data_lock:
                last_mouse_position = pyautogui.position()
        
        # Toggle features
        if keyboard.is_pressed(ANTI_RECOIL_TOGGLE_KEY):
            anti_recoil_active = not anti_recoil_active
            print(f"Anti-recoil {'ON' if anti_recoil_active else 'OFF'}")
            time.sleep(0.5)  # Debounce
            
        if keyboard.is_pressed(AIMBOT_TOGGLE_KEY):
            aimbot_active = not aimbot_active
            print(f"Aimbot {'ON' if aimbot_active else 'OFF'}")
            time.sleep(0.5)
            
        # Shooting state detection
        shooting = keyboard.is_pressed(SHOOT_KEY)
        time.sleep(0.01)

# ======================
# MAIN PROGRAM
# ======================
if __name__ == "__main__":
    print("===== GAME ASSISTANCE TOOL =====")
    print(f"Anti-Recoil: Press {ANTI_RECOIL_TOGGLE_KEY} to toggle")
    print(f"Aimbot: Press {AIMBOT_TOGGLE_KEY} to toggle")
    print("================================")
    
    # Start subsystems
    Thread(target=anti_recoil_controller, daemon=True).start()
    Thread(target=aimbot_controller, daemon=True).start()
    Thread(target=monitor_inputs, daemon=True).start()
    
    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        program_running = False
        print("\nProgram terminated")
