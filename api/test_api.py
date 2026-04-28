import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def print_response(res):
    print(f"  --> Status Code: {res.status_code}")
    try:
        # Check if there is a JSON response to show
        json_data = res.json()
        print(f"  --> API Response: {json.dumps(json_data, indent=2)}")
        return json_data
    except ValueError:
        print(f"  --> API Response: {res.text}")
        return None

def test_api():
    print(f"[{BASE_URL}] Starting Detailed API Movement Test...\n")

    print("--- Listing Available Ports ---")
    try:
        res = requests.get(f"{BASE_URL}/list_ports")
        ports_data = print_response(res)
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return

    if not ports_data or not ports_data.get("ports"):
        print("No ports available or API error. Make sure your robot is plugged in.")
        return
        
    print("\nAvailable ports:")
    for p in ports_data["ports"]:
        print(f" - {p['device']} ({p['description']})")
        
    selected_port = input("\nEnter the exact port name to connect (e.g., COM20 or /dev/ttyUSB0): ").strip()
    
    if not selected_port:
        print("No port selected. Exiting.")
        return

    print(f"\n--- Connecting to {selected_port} ---")
    res = requests.post(f"{BASE_URL}/connect", json={"port": selected_port})
    connect_data = print_response(res)
    
    if not connect_data or connect_data.get("status") != "success":
        print("Connection failed. Exiting test.")
        return

    print("\nConnection Successful!")
    print("Delays have been added between steps to allow physical machine movements to be observed.\n")
    time.sleep(1)

    # 1. Soft transition to Start/Home position (Z=-150)
    print("Step 1: Soft transition to Start/Home position (Z=-150) (takes 2 sec)")
    data = {"x": 0, "y": 0, "z": -150, "ms": 2000}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    input("Press Enter to continue...")

    print("\nStep 1.5: Reading current Motor and End-effector positions")
    print("  --- /get_mot_pos ---")
    mot_pos_res = requests.get(f"{BASE_URL}/get_mot_pos")
    print_response(mot_pos_res)
    
    print("  --- /get_ee_pos ---")
    ee_pos_res = requests.get(f"{BASE_URL}/get_ee_pos")
    print_response(ee_pos_res)
    input("Press Enter to continue...")


    # 2. Smooth movement right on the X-axis
    print("\nStep 2: Moving right to point X=40 (2 sec)")
    data = {"x": 40, "y": 0, "z": -150, "ms": 2000}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    input("Press Enter to continue...")

    print("\nStep 1.5: Reading current Motor and End-effector positions")
    print("  --- /get_mot_pos ---")
    mot_pos_res = requests.get(f"{BASE_URL}/get_mot_pos")
    print_response(mot_pos_res)
    
    print("  --- /get_ee_pos ---")
    ee_pos_res = requests.get(f"{BASE_URL}/get_ee_pos")
    print_response(ee_pos_res)
    input("Press Enter to continue...")


    # 3. Smooth movement left on the X-axis (longer distance)
    print("\nStep 3: Moving left to point X=-40 (3 sec)")
    data = {"x": -40, "y": 0, "z": -150, "ms": 3000}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    input("Press Enter to continue...")

    # 4. Return to center point
    print("\nStep 4: Returning to center (X=0) (1.5 sec)")
    data = {"x": 0, "y": 0, "z": -150, "ms": 1500}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    input("Press Enter to continue...")

    # 5. Read instantaneous position and print to terminal
    print("\nStep 5: Reading current Motor and End-effector positions")
    print("  --- /get_mot_pos ---")
    mot_pos_res = requests.get(f"{BASE_URL}/get_mot_pos")
    print_response(mot_pos_res)
    
    print("  --- /get_ee_pos ---")
    ee_pos_res = requests.get(f"{BASE_URL}/get_ee_pos")
    print_response(ee_pos_res)
    input("Press Enter to continue...")

    # 6. Magnet Test (Grab Object)
    print("\nStep 6: Fast instantaneous drop to Z=-200 to grab object (move_pos will drop instantly!)")
    data = {"x": 0, "y": 0, "z": -200}
    res = requests.post(f"{BASE_URL}/move_pos", json=data)
    print_response(res)
    input("Press Enter to continue...")
    
    print("\n  -> Turning Magnet ON (grab=1)")
    res = requests.post(f"{BASE_URL}/grab", json={"state": 1})
    print_response(res)
    input("Press Enter to continue...")

    print("\n  -> Turning Magnet OFF (grab=0)")
    res = requests.post(f"{BASE_URL}/grab", json={"state": 0})
    print_response(res)
    input("Press Enter to continue...")

    # 7. Final - Finish by rising to Home position
    print("\nStep 7: Operation finished. Gently rising to Home position (1.5 sec)") 
    data = {"x": 0, "y": 0, "z": -150, "ms": 1500}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    input("Press Enter to continue...")
    
    print("\nDetailed test completed successfully!")

if __name__ == "__main__":
    test_api()
