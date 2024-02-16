import socket
import threading

# Choosing Nickname
nickname = input("Choose your nickname: ")
if nickname == 'admin':
    
    passwd = input("enter password : ")
# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((socket.gethostbyname(socket.gethostname()), 55557))

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
                        print('wrong password')
                        stopThread = True
                elif next_message == 'BAN':
                    print('Connection refused due to ban')
                    client.close()
                    stopThread = True
            else:
                print(message)
        except:
            # Close Connection When Error
            print("An error occured!")
            client.close()
            break

# Sending Messages To Server
def write():
    while True:
        if stopThread == True:
            break

        message = f'{format(nickname)}: {format(input(""))}'
        if message.split(" ")[1].startswith('/'):
            if nickname == 'admin':
                if message.split(" ")[1].startswith('/kick'):
                    client.send(f'KICK {message.split(" ")[2]}'.encode('ascii'))
                elif message.split(" ")[1].startswith('/ban'):
                    client.send(f'BAN {message.split(" ")[2]}'.encode('ascii'))
            else:
                print("You are not admin")
        else:
            client.send(message.encode('ascii'))

# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()