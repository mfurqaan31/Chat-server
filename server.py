import socket, threading, ssl, shutil, os

host = 'localhost'
port = 55557
active_sockets=0

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('ssl.pem','private.key')

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = context.wrap_socket(server, server_side=True)
server.bind((host, port))
server.listen()

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    global active_sockets

    while True:
        try:
            place_message = message = client.recv(1024)
            if place_message.decode('ascii').split(" ")[0] == 'KICK':
                if nicknames[clients.index(client)] == 'admin':
                    nameToKick = place_message.decode('ascii').split(" ")[1]
                    kickUser(nameToKick)
                else:
                    client.send('Command was reduced'.encode('ascii'))
            elif place_message.decode('ascii').split(" ")[0] == 'BAN':
                if nicknames[clients.index(client)] == 'admin':
                    nameToBan = place_message.decode('ascii').split(" ")[1]
                    with open('banlist.txt', 'a') as f:
                        f.write(nameToBan + '\n')
                    print(f"{nameToBan} has been banned.")
                    kickUser(nameToBan)
                else:
                    client.send('Command was reduced'.encode('ascii'))
            elif place_message.decode("ascii").split(" ")[0]=="MEMBERS":
                for i in nicknames:
                    if i!="admin":
                        client.send(i.encode("ascii"))
            elif place_message.decode('ascii').startswith("Filename"):
                file_path = place_message.decode('ascii').split(" ", 1)[1]
                print(f"Uploaded file path: {file_path}")
                broadcast(f"New file received in Downloads:".encode('ascii'))
                file=os.path.basename(file_path)
                downloads=os.path.join(os.path.expanduser("~"), "Downloads")
                folder_path = os.path.join(downloads, "Server Files")
                os.makedirs(folder_path, exist_ok=True)
                destination_path = os.path.join(folder_path, file)
                shutil.copy(file_path, destination_path)
            else:
                broadcast(message)
        except:
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                broadcast('{} left!'.format(nickname).encode('ascii'))
                nicknames.remove(nickname)
                active_sockets -= 1 
                print(f"Number of active connections: {active_sockets}")
                break

def receive():
    global active_sockets 
    print(f"Server is listening")
    while True:
        client, address = server.accept()
        active_sockets += 1  
        print(f"Connected with {str(address)}")
        print(f"Number of active connections: {active_sockets}")
        client.send('MANU'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        if nickname in nicknames:
            client.send("Duplicate".encode("ascii"))
            print(f"Client having IP {address} is disconnected")
            client.close()
            continue
        with open('banlist.txt','r') as f:
            bans = f.readlines()
        if nickname+'\n' in bans:
            client.send('BAN'.encode('ascii'))
            client.close()
            continue
        if nickname == 'admin':
            client.send('PASS'.encode('ascii'))
            password = client.recv(1024).decode('ascii')
            if password != 'password':
                client.send('WRONG'.encode('ascii'))
                client.close()
                continue
        nicknames.append(nickname)
        clients.append(client)
        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode('ascii'))
        client.send('Connected to server!'.encode('ascii'))
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()
        print(f"Number of active connections: {active_sockets}")

def kickUser(name):
    if name in nicknames:
        nameIndex = nicknames.index(name)
        client = clients[nameIndex]
        clients.remove(client)
        client.send('You have been kicked by the admin'.encode('ascii'))
        client.close()
        nicknames.remove(name)
        broadcast("{} was kicked by admin.".format(name).encode('ascii'))

receive()
