import socket,threading, ssl,os,maskpass

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

host = 'localhost'
context.load_verify_locations('ssl.pem')
nickname = input("Choose your nickname: ")
if nickname == 'admin':
    passwd=maskpass.askpass(mask="*")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = context.wrap_socket(client, server_hostname=host)
client.connect((host, 55557))

stopThread = False

def receive():
    global stopThread
    while True:
        try:
            if stopThread:
                break
            message = client.recv(1024).decode('ascii')
            if not message:
                print("Disconnected from server.")
                stopThread = True
                break
            if message == 'MANU':
                client.send(nickname.encode('ascii'))
                next_message = client.recv(1024).decode('ascii')
                if next_message == 'PASS':
                    client.send(passwd.encode('ascii'))
                    if client.recv(1024).decode('ascii') == 'WRONG':
                        print('wrong password')
                        stopThread = True
                elif next_message == 'BAN':
                    print('Connection refused due to ban')
                    client.close()
                    stopThread = True

                elif next_message == "Duplicate":
                    print("Username already exists quit the server and login through a new username")
                    client.close()
                    stopThread=True
            else:
                print(message)
                if message.startswith("File received at:"):
                    pass
        except Exception as e:
            print("An error occurred:", e)
            client.close()
            stopThread = True
            break

def write():
    while True:
        if stopThread:
            break
        message = input()
        if message.startswith('/'):
            command_parts=message.split(" ")
            if len(command_parts)>=1:
                if command_parts[0]=='/file':
                    file_path=command_parts[1].strip()
                    if os.path.exists(file_path):
                        client.send(f'Filename {file_path}'.encode('ascii'))
                    else:
                        print("File not found!")
                elif nickname == 'admin':
                    if command_parts[0] == '/kick':
                        client.send(f'KICK {command_parts[1]}'.encode('ascii'))
                    elif command_parts[0] == '/ban':
                        client.send(f'BAN {command_parts[1]}'.encode('ascii'))
                    elif command_parts[0] == '/members':
                        client.send(f'MEMBERS'.encode('ascii'))
                else:
                    print("You are not admin")
            else:
                print("Invalid command format")
        else:
            client.send(f'{nickname}: {message}'.encode('ascii'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
