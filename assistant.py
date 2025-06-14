import pyautogui
import keyboard
import time
import cv2
import numpy as np
import os
import json
import pytesseract
from PIL import Image
from threading import Thread, Lock
from llama_cpp import Llama  # For local GGUF models

# ======================
# CONFIGURATION SETTINGS
# ======================
SETUP_HOTKEY = 'ctrl+s'
ANTI_RECOIL_TOGGLE_KEY = 'f1'
AIMBOT_TOGGLE_KEY = 'f2'
MONEY_REGION = (100, 50, 200, 40)
ROUND_REGION = (900, 50, 100, 40)
MIN_MOTION_SIZE = 500
AIM_SMOOTHNESS = 0.85
MODEL_PATH = "models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"  # Local GGUF model

# ======================
# GLOBAL STATE
# ======================
game_info = {"game": "unknown", "team": "unknown"}
setup_mode = False
anti_recoil_active = False
aimbot_active = False
program_running = True
llm = None  # Will hold our local AI model
data_lock = Lock()

# ======================
# AI MODEL MANAGEMENT
# ======================
def load_ai_model():
    global llm
    try:
        # Check if model file exists
        if not os.path.exists(MODEL_PATH):
            print(f"Model not found at: {MODEL_PATH}")
            print("Please download a suitable GGUF model and place in models/ folder")
            return False
        
        # Load the model with optimized settings
        print("Loading AI model...")
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,  # Context size
            n_threads=4,  # Use 4 CPU cores
            n_gpu_layers=0,  # 0 for CPU-only, set to layers count for GPU offloading
            verbose=False
        )
        print("AI model loaded successfully")
        return True
    except Exception as e:
        print(f"Failed to load AI model: {str(e)}")
        return False

# ======================
# SETUP SYSTEM
# ======================
def save_game_info():
    global game_info, setup_mode
    print("\n===== GAME SETUP =====")
    game_info["game"] = input("Enter game name (e.g., cs2, valorant): ")
    game_info["team"] = input("Enter your team (e.g., CT, T): ")
    
    # Save to config file
    with open('game_config.json', 'w') as f:
        json.dump(game_info, f)
    
    print(f"Configuration saved: Playing {game_info['game']} as {game_info['team']}")
    print("=======================")
    setup_mode = False

# ======================
# ECONOMY MANAGER (LOCAL AI)
# ======================
def get_money_and_round():
    try:
        # Capture money region
        money_img = pyautogui.screenshot(region=MONEY_REGION)
        money_text = pytesseract.image_to_string(money_img).strip()
        money_amount = int(''.join(filter(str.isdigit, money_text)))
        
        # Capture round region
        round_img = pyautogui.screenshot(region=ROUND_REGION)
        round_text = pytesseract.image_to_string(round_img).strip()
        current_round = int(''.join(filter(str.isdigit, round_text)))
        
        return money_amount, current_round
    except:
        return None, None

def get_local_ai_recommendation(money, round_num):
    if not llm:
        return None
    
    try:
        prompt = f"""
        <s>[INST] You are an esports coach specializing in {game_info['game']}. 
        Recommend equipment for:
        - Team: {game_info['team']}
        - Money: ${money}
        - Round: {round_num}/30
        
        Consider:
        1. Current meta strategies
        2. Expected enemy equipment
        3. Team economy status
        4. Map tactics
        
        Output in JSON format only:
        {{
            "recommendation": "[Buy/Save/Eco]",
            "primary_weapon": "[Weapon]",
            "secondary_weapon": "[Pistol]",
            "equipment": ["Item1", "Item2"],
            "utility": ["Grenade1", "Grenade2"],
            "reason": "[Brief explanation]"
        }}
        [/INST]
        """
        
        # Generate response
        response = llm(
            prompt,
            max_tokens=256,
            stop=["</s>"],
            echo=False,
            temperature=0.3  # Lower for more consistent results
        )
        
        # Extract JSON from response
        output = response['choices'][0]['text'].strip()
        json_start = output.find('{')
        json_end = output.rfind('}') + 1
        json_str = output[json_start:json_end]
        
        return json.loads(json_str)
    except Exception as e:
        print(f"AI error: {str(e)}")
        return None

# ======================
# MOTION-BASED AIMBOT
# ======================
prev_frame = None

def detect_moving_players():
    global prev_frame
    frame = np.array(pyautogui.screenshot())
    
    if prev_frame is None:
        prev_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        return []
    
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    frame_diff = cv2.absdiff(prev_frame, gray_frame)
    _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
    
    # Find moving objects
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    players = []
    for cnt in contours:
        if cv2.contourArea(cnt) > MIN_MOTION_SIZE:
            x, y, w, h = cv2.boundingRect(cnt)
            players.append((x + w//2, y + h//2))  # Return center points
    
    prev_frame = gray_frame
    return players

def move_mouse_smoothly(target):
    current_x, current_y = pyautogui.position()
    target_x, target_y = target
    
    # Calculate smoothed movement
    new_x = current_x + (target_x - current_x) * AIM_SMOOTHNESS
    new_y = current_y + (target_y - current_y) * AIM_SMOOTHNESS
    
    pyautogui.moveTo(new_x, new_y, _pause=False)

def aim_at_nearest_target():
    targets = detect_moving_players()
    if not targets:
        return False
    
    # Get screen center
    screen_width, screen_height = pyautogui.size()
    screen_center = (screen_width // 2, screen_height // 2)
    
    # Find closest target to center
    closest = min(targets, key=lambda p: np.sqrt((p[0]-screen_center[0])**2 + (p[1]-screen_center[1])**2))
    
    move_mouse_smoothly(closest)
    return True

# ======================
# INPUT HANDLING
# ======================
def monitor_inputs():
    global setup_mode, anti_recoil_active, aimbot_active
    
    while program_running:
        # Toggle features
        if keyboard.is_pressed(SETUP_HOTKEY):
            setup_mode = True
            print("Setup mode activated")
            time.sleep(1)  # Debounce
            
        if keyboard.is_pressed(ANTI_RECOIL_TOGGLE_KEY):
            anti_recoil_active = not anti_recoil_active
            print(f"Anti-recoil {'ON' if anti_recoil_active else 'OFF'}")
            time.sleep(0.5)
            
        if keyboard.is_pressed(AIMBOT_TOGGLE_KEY):
            aimbot_active = not aimbot_active
            print(f"Motion Aim {'ON' if aimbot_active else 'OFF'}")
            time.sleep(0.5)
        
        time.sleep(0.01)

# ======================
# ECONOMY THREAD
# ======================
def economy_manager():
    last_check_time = 0
    last_recommendation = None
    
    while program_running:
        current_time = time.time()
        
        # Check every 15 seconds
        if current_time - last_check_time > 15:
            money, round_num = get_money_and_round()
            
            if money is not None:
                # Get AI recommendation
                recommendation = get_local_ai_recommendation(money, round_num)
                
                if recommendation:
                    last_recommendation = recommendation
                    print("\n===== ECONOMY RECOMMENDATION =====")
                    print(f"Round {round_num} | ${money}")
                    print(f"Recommendation: {recommendation['recommendation']}")
                    print(f"Primary: {recommendation['primary_weapon']}")
                    print(f"Secondary: {recommendation['secondary_weapon']}")
                    print(f"Equipment: {', '.join(recommendation['equipment'])}")
                    print(f"Utility: {', '.join(recommendation['utility'])}")
                    print(f"Reason: {recommendation['reason']}")
                    print("================================")
            
            last_check_time = current_time
        
        time.sleep(1)

# ======================
# MAIN PROGRAM
# ======================
if __name__ == "__main__":
    # Try to load existing config
    if os.path.exists('game_config.json'):
        with open('game_config.json', 'r') as f:
            game_info = json.load(f)
        print(f"Loaded config: Playing {game_info['game']} as {game_info['team']}")
    else:
        print("Game config not found. Press Ctrl+S to set up")
    
    # Load AI model
    if not load_ai_model():
        print("Running without AI recommendations")
    
    print("===== GAME ASSISTANCE TOOL =====")
    print(f"Press {SETUP_HOTKEY} to configure game/team")
    print(f"Anti-Recoil: Press {ANTI_RECOIL_TOGGLE_KEY} to toggle")
    print(f"Motion Aim: Press {AIMBOT_TOGGLE_KEY} to toggle")
    print("================================")
    
    # Start subsystems
    Thread(target=monitor_inputs, daemon=True).start()
    Thread(target=economy_manager, daemon=True).start()
    
    # Main loop
    try:
        while program_running:
            if setup_mode:
                save_game_info()
            
            if aimbot_active:
                target_acquired = aim_at_nearest_target()
                if target_acquired and keyboard.is_pressed('space'):
                    pyautogui.click()
            
            time.sleep(0.05)
    except KeyboardInterrupt:
        program_running = False
        print("\nProgram terminated")
