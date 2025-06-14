import pyautogui
import keyboard
import time
import cv2
import numpy as np
import os
from threading import Thread, Lock
import pytesseract
from PIL import Image

# ======================
# VERSION INFORMATION
# ======================
__version__ = "1.1.0-beta"
__release_date__ = "2025-06-15"

# ======================
# CONFIGURATION SETTINGS
# ======================
ANTI_RECOIL_TOGGLE_KEY = 'f1'
AIMBOT_TOGGLE_KEY = 'f2'
HEAD_DETECTION_TOGGLE_KEY = 'f3'
SHOOT_KEY = 'ctrl'  # Key used for shooting in-game
ENEMY_COLOR = (0, 0, 255)  # BGR color to detect (red in this example)
COLOR_TOLERANCE = 50  # Color detection sensitivity
SCAN_RADIUS = 300  # Pixels around crosshair to search for enemies
ANTI_RECOIL_STRENGTH = 0.5  # Recoil correction speed (0-1)
PLAYER_TEAM = 'ct'  # 'ct' or 't' - your team
HEAD_SCAN_INTERVAL = 0.5  # Seconds between head scans
HEAD_MATCH_THRESHOLD = 0.7  # Confidence threshold (0-1)
HEAD_DIRECTORY = "Function/heads"  # Path to head templates

# ======================
# GLOBAL STATE
# ======================
anti_recoil_active = False
aimbot_active = False
head_detection_active = False
shooting = False
last_mouse_position = pyautogui.position()
program_running = True
data_lock = Lock()

# ======================
# HEAD DETECTION SYSTEM
# ======================
def load_head_templates():
    """Load head templates from directory structure"""
    templates = {'ct': [], 't': []}
    
    # Create directories if they don't exist
    os.makedirs(os.path.join(HEAD_DIRECTORY, 'ct'), exist_ok=True)
    os.makedirs(os.path.join(HEAD_DIRECTORY, 't'), exist_ok=True)
    
    for team in ['ct', 't']:
        team_path = os.path.join(HEAD_DIRECTORY, team)
        for filename in os.listdir(team_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(team_path, filename)
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    # Convert to grayscale for better matching
                    if img.shape[2] == 4:  # Handle alpha channel
                        mask = img[:,:,3] == 0
                        img[mask] = [0, 0, 0, 0]
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    templates[team].append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    
    print(f"Loaded {len(templates['ct'])} CT heads and {len(templates['t'])} T heads")
    return templates

# Load templates at startup
HEAD_TEMPLATES = load_head_templates()

def find_head_position():
    """Detect enemy heads using template matching"""
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
    screen_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    
    # Determine enemy team based on player's team
    enemy_team = 't' if PLAYER_TEAM == 'ct' else 'ct'
    best_match = None
    best_val = 0
    
    # Search for enemy heads
    for template in HEAD_TEMPLATES[enemy_team]:
        if template.shape[0] > screen_img.shape[0] or template.shape[1] > screen_img.shape[1]:
            continue
            
        # Template matching with different methods
        methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
        for method in methods:
            res = cv2.matchTemplate(screen_img, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            # For TM_CCOEFF_NORMED and TM_CCORR_NORMED, higher is better
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_template = template
                best_method = method
    
    # Check if we found a valid match
    if best_val < HEAD_MATCH_THRESHOLD:
        return None
    
    # Calculate head center position
    h, w = best_template.shape
    center_x = best_loc[0] + w//2 + scan_area[0]
    center_y = best_loc[1] + h//2 + scan_area[1]
    
    # AI-powered verification using OCR
    if verify_head_with_ai(screenshot, best_loc, (w, h)):
        return (center_x, center_y)
    
    return None

def verify_head_with_ai(screenshot, location, size):
    """Use OCR to verify if the detected region contains player text"""
    try:
        # Extract the region around the detected head
        x, y = location
        w, h = size
        expanded_region = (
            max(0, x - 50),
            max(0, y - 20),
            min(screenshot.width, x + w + 50),
            min(screenshot.height, y + h + 20)
        )
        region_img = screenshot.crop(expanded_region)
        
        # Preprocess image for better OCR
        gray_img = region_img.convert('L')
        sharp_img = gray_img.filter(ImageFilter.SHARPEN)
        
        # Use OCR to detect text
        text = pytesseract.image_to_string(sharp_img, config='--psm 7')
        
        # Check for player-like text (mix of letters and numbers)
        if re.search(r'[a-zA-Z]{2,}\d+', text):
            return True
    except Exception as e:
        print(f"AI verification error: {e}")
    
    return False

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
        if aimbot_active or head_detection_active:
            current_time = time.time()
            
            # Reduce CPU usage when no enemies detected
            if current_time - last_detection_time > 2.0:  # 2-second cooldown
                time.sleep(0.1)
                continue
            
            # Use head detection if enabled, otherwise use color detection
            if head_detection_active:
                enemy_pos = find_head_position()
            else:
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
    global shooting, anti_recoil_active, aimbot_active, head_detection_active, last_mouse_position
    
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
            if aimbot_active:
                head_detection_active = False
            print(f"Color Aimbot {'ON' if aimbot_active else 'OFF'}")
            time.sleep(0.5)
            
        if keyboard.is_pressed(HEAD_DETECTION_TOGGLE_KEY):
            head_detection_active = not head_detection_active
            if head_detection_active:
                aimbot_active = False
            print(f"Head Detection {'ON' if head_detection_active else 'OFF'}")
            time.sleep(0.5)
            
        # Shooting state detection
        shooting = keyboard.is_pressed(SHOOT_KEY)
        time.sleep(0.01)

# ======================
# MAIN PROGRAM
# ======================
if __name__ == "__main__":
    print("===== ADVANCED GAME ASSISTANCE TOOL =====")
    print(f"Version: {__version__} ({__release_date__})")
    print(f"Anti-Recoil: Press {ANTI_RECOIL_TOGGLE_KEY} to toggle")
    print(f"Color Aimbot: Press {AIMBOT_TOGGLE_KEY} to toggle")
    print(f"Head Detection: Press {HEAD_DETECTION_TOGGLE_KEY} to toggle")
    print("========================================")
    
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