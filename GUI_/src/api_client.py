import requests

class DeltaAPIClient:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.position = [0, 0, 0] # cached motor pos [m1, m2, m3]
        self.ee_position = [0, 0, 0] # cached ee pos [x, y, z]
        self.is_connected = False

    def list_ports(self):
        """Fetch available serial ports from API."""
        try:
            res = self.session.get(f"{self.base_url}/list_ports", timeout=2)
            if res.status_code == 200:
                data = res.json()
                return [(p['device'], p['description']) for p in data.get("ports", [])]
        except Exception:
            pass
        return []

    def connect(self, port):
        """Connect the backend API to the hardware."""
        try:
            res = self.session.post(f"{self.base_url}/connect", json={"port": port}, timeout=5)
            if res.status_code == 200 and res.json().get("status") == "success":
                self.is_connected = True
                return True
        except Exception:
            pass
        self.is_connected = False
        return False

    def disconnect(self):
        """Disconnect the backend API from hardware."""
        try:
            self.session.post(f"{self.base_url}/disconnect", timeout=2)
        except Exception:
            pass
        self.is_connected = False

    def update(self):
        """Update telemetry data from backend in one combined request."""
        if not self.is_connected:
            return
        
        try:
            res = self.session.get(f"{self.base_url}/get_telemetry", timeout=0.5)
            if res.status_code == 200:
                d = res.json()
                if "error" not in d:
                    self.position = [d.get("m1", 0), d.get("m2", 0), d.get("m3", 0)]
                    self.ee_position = [d.get("x", 0), d.get("y", 0), d.get("z", 0)]
        except Exception:
            pass

    def move_pos(self, x, y, z, ms=None):
        """Move API endpoint - delegates IK to backend."""
        if not self.is_connected:
            return
            
        data = {"x": x, "y": y, "z": z}
        endpoint = "/move_pos"
        
        if ms is not None:
            data["ms"] = ms
            endpoint = "/move_pos_traj"
            
        try:
            # We don't care about the response for high-freq tracking, so keep timeout small
            # except if it's a long trajectory, but GUI generally sends continuous points or instantaneous jumps.
            self.session.post(f"{self.base_url}{endpoint}", json=data, timeout=0.5)
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass

    def pick(self, state):
        """Enable or disable magnet/picker."""
        if not self.is_connected:
            return
        try:
            val = 1 if state else 0
            self.session.post(f"{self.base_url}/grab", json={"state": val}, timeout=1)
        except Exception:
            pass
