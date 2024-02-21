import socket
import threading
import ssl
import os

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

host = 'localhost'
context.load_verify_locations('ssl.pem')
# Choosing Nickname
nickname = input("Choose your nickname: ")
if nickname == 'admin':
    passwd = input("enter password : ")
# Connecting To Server

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client = context.wrap_socket(client, server_hostname=host)
client.connect((host, 55557))

stopThread = False


def receive():
    while True:
        global stopThread
        if stopThread:
            break
        try:
            # Receive Message From Server
            # If 'MANU' Send Nickname
            message = client.recv(1024).decode('ascii')
            if message == 'MANU':
                client.send(nickname.encode('ascii'))
                next_message = client.recv(1024).decode('ascii')
                if next_message == 'PASS':
                    client.send(passwd.encode('ascii'))
                    if client.recv(1024).decode('ascii') == 'WRONG':
                        print('wrong password,press ctrl C to exit')
                        stopThread = True
                elif next_message == 'BAN':
                    print('Connection refused due to ban ,press ctrl c to exit')
                    client.close()
                    stopThread = True
                elif next_message == 'DUPLICATE':
                    print('this user already exists ,press control C to stop execution')
                    client.close()
                    stopThread = True
                elif next_message == 'MEMBERS':
                    print('are the members') 
            else:
                print(message)
                if message.startswith("File received at:"):
                    pass
        except:
            # Close Connection When Error
            print("An error occurred!")
            client.close()
            break

# Sending Messages To Server
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
                        print(f'invalid command')
                else:
                    print("You are not admin")
            else:
                print("Invalid command format")
        else:
            client.send(f'{nickname}: {message}'.encode('ascii'))



# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)

write_thread.start()

receive_thread.join()
write_thread.join()