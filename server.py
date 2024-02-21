import socket,threading,ssl,sys

host = 'localhost'
port = 55558

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

context.load_cert_chain('ssl.pem','private.key')
# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = context.wrap_socket(server, server_side=True)
#allow to reconnect without having to increment ip addr
server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
def broadcast(message):
    for client in clients:
       client.send(message)
            
    
def handle(client,address):
    while True:
        try:
            # Broadcasting Messages
            place_message = message = client.recv(1024)

            if place_message.decode('ascii').split(" ")[0] == 'KICK':
                if nicknames[clients.index(client)] == 'admin':
                    nameToKick = place_message.decode('ascii').split(" ")[1]
                    kickUser(nameToKick)
                else:
                    client.send('Command was reduced(not an admin)'.encode('ascii'))
            elif place_message.decode('ascii').split(" ")[0] == 'BAN':
                if nicknames[clients.index(client)] == 'admin':
                    nameToBan = place_message.decode('ascii').split(" ")[1]
                    
                    with open('banlist.txt', 'a') as f:
                        f.write(nameToBan + '\n')
                    print(f"{nameToBan} has been banned.")
                    kickUser(nameToBan)
                else:
                    client.send('Command was reduced(not an admin)'.encode('ascii'))
            else:
                broadcast(message)
        except:
            
        # Removing And Closing Clients
            if client in clients:
                index = clients.index(client)
                clients.remove(client)   
                nickname = nicknames[index]
                broadcast('{} left!'.format(nickname).encode('ascii'))
                print(f'client of ip {address} is disconnected')
                nicknames.remove(nickname)
                client.close()
                break

def receive():
    print(f"Server is listening")
    while True:
        # Accept Connection
        client, address = server.accept()
        print("Connected with {}".format(str(address)))

        # Request And Store Nickname
        client.send('MANU'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        if nickname in nicknames:
            client.send('DUPLICATE'.encode('ascii'))
            print(f'client having ip {address} is disconnected')
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

        # Print And Broadcast Nickname
        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode('ascii'))
        client.send('Connected to server!'.encode('ascii'))

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,address,))
        thread.start()
        #print(f"number of active connections is : {threading.active_count() - 1}")


def kickUser(name):
    if name in nicknames:
        nameIndex = nicknames.index(name)
        client = clients[nameIndex]
        clients.remove(client)
        client.send('you have been kicked by the admin'.encode('ascii'))
        client.close()
        nicknames.remove(name)
        broadcast("{} was kicked by admin.".format(name).encode('ascii'))

if __name__ == "__main__":
    receive()
