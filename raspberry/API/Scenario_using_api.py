import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def get_positions():
    print("\n--- Getting Positions ---")
    try:
        response = requests.get(f"{BASE_URL}/get_ee_pos")
        if response.status_code == 200:
            print("End-Effector Position:", response.json())
        else:
            print("Error:", response.text)
            
        response = requests.get(f"{BASE_URL}/get_mot_pos")
        if response.status_code == 200:
            print("Motor Positions:", response.json())
        else:
            print("Error:", response.text)
    except Exception as e:
        print("Error connecting to API (Is the server running?):", e)

def move_to(x, y, z, ms=None):
    print(f"\n--- Moving to: ({x}, {y}, {z}) ---")
    data = {"x": x, "y": y, "z": z}
    try:
        if ms:
            data["ms"] = ms
            print(f"Trajectory movement ({ms} ms)")
            response = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
        else:
            print("Direct movement")
            response = requests.post(f"{BASE_URL}/move_pos", json=data)
            
        print("Response:", response.json())
    except Exception as e:
        print("Error sending move command:", e)

def grab(state):
    action = "Grabbing" if state else "Releasing"
    print(f"\n--- {action} ---")
    try:
        response = requests.post(f"{BASE_URL}/grab", json={"state": state})
        print("Response:", response.json())
    except Exception as e:
        print("Error sending grab command:", e)

def delay(ms):
    print(f"\n--- Waiting: {ms} ms ---")
    try:
        response = requests.post(f"{BASE_URL}/delay", json={"ms": ms})
        print("Response:", response.json())
    except Exception as e:
        print("Error sending delay command:", e)

def main():
    print("Starting Test Scenario...")
    print("Please ensure that 'app.py' is running in the background and serving the API.\n")
    
    # 1. Read current positions
    get_positions()
    time.sleep(1)
    
    # 2. Move above the object
    move_to(0, 0, -200, ms=1500)  # Trajectory movement (1.5 seconds)
    delay(500)
    
    # 3. Move down slowly (or directly)
    move_to(0, 0, -250)           # Direct movement
    delay(500)
    
    # 4. Grab the object
    grab(1)
    delay(500)
    
    # 5. Move back up
    move_to(0, 0, -200, ms=1000)
    delay(500)
    
    # 6. Move to target location (e.g., X=50, Y=50)
    move_to(50, 50, -200, ms=2000)
    delay(500)
    
    # 7. Move down at the target location
    move_to(50, 50, -250)
    delay(500)
    
    # 8. Release the object
    grab(0)
    delay(500)
    
    # 9. Return to start (center) position
    move_to(0, 0, -200, ms=1500)
    
    # 10. Check final status again
    get_positions()
    
    print("\nScenario Completed!")

if __name__ == "__main__":
    main()
