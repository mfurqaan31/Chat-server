import socket
import threading
import pickle
import os
import sys

groups = {}
fileTransferCondition = threading.Condition()

def create_group(admin, client):
    return {
        'admin': admin,
        'clients': {admin: client},
        'offline_messages': {},
        'all_members': {admin},
        'online_members': {admin},
        'join_requests': set(),
        'wait_clients': {}
    }

def disconnect_from_group(groupname, username):
    groups[groupname]['online_members'].remove(username)
    del groups[groupname]['clients'][username]

def connect_to_group(groupname, username, client):
    groups[groupname]['online_members'].add(username)
    groups[groupname]['clients'][username] = client

def send_message_to_group(groupname, message, username):
    for member in groups[groupname]['online_members']:
        if member != username:
            groups[groupname]['clients'][member].send(bytes(username + ": " + message, "utf-8"))

def pycon_chat(client, username, groupname):
    while True:
        msg = client.recv(1024).decode("utf-8")
        if msg == "/viewRequests":
            client.send(b"/viewRequests")
            client.recv(1024).decode("utf-8")
            if username == groups[groupname]['admin']:
                client.send(b"/sendingData")
                client.recv(1024)
                client.send(pickle.dumps(groups[groupname]['join_requests']))
            else:
                client.send(b"You're not an admin.")
        elif msg == "/approveRequest":
            client.send(b"/approveRequest")
            client.recv(1024).decode("utf-8")
            if username == groups[groupname]['admin']:
                client.send(b"/proceed")
                username_to_approve = client.recv(1024).decode("utf-8")
                if username_to_approve in groups[groupname]['join_requests']:
                    groups[groupname]['join_requests'].remove(username_to_approve)
                    groups[groupname]['all_members'].add(username_to_approve)
                    if username_to_approve in groups[groupname]['wait_clients']:
                        groups[groupname]['wait_clients'][username_to_approve].send(b"/accepted")
                        connect_to_group(groupname, username_to_approve, groups[groupname]['wait_clients'][username_to_approve])
                        del groups[groupname]['wait_clients'][username_to_approve]
                    print("Member Approved:", username_to_approve, "| Group:", groupname)
                    client.send(b"User has been added to the group.")
                else:
                    client.send(b"The user has not requested to join.")
            else:
                client.send(b"You're not an admin.")
        elif msg == "/disconnect":
            client.send(b"/disconnect")
            client.recv(1024).decode("utf-8")
            disconnect_from_group(groupname, username)
            print("User Disconnected:", username, "| Group:", groupname)
            break
        elif msg == "/messageSend":
            client.send(b"/messageSend")
            message = client.recv(1024).decode("utf-8")
            send_message_to_group(groupname, message, username)
        elif msg == "/waitDisconnect":
            client.send(b"/waitDisconnect")
            del groups[groupname]['wait_clients'][username]
            print("Waiting Client:", username, "Disconnected")
            break
        elif msg == "/allMembers":
            client.send(b"/allMembers")
            client.recv(1024).decode("utf-8")
            client.send(pickle.dumps(groups[groupname]['all_members']))
        elif msg == "/onlineMembers":
            client.send(b"/onlineMembers")
            client.recv(1024).decode("utf-8")
            client.send(pickle.dumps(groups[groupname]['online_members']))
        elif msg == "/changeAdmin":
            client.send(b"/changeAdmin")
            client.recv(1024).decode("utf-8")
            if username == groups[groupname]['admin']:
                client.send(b"/proceed")
                new_admin_username = client.recv(1024).decode("utf-8")
                if new_admin_username in groups[groupname]['all_members']:
                    groups[groupname]['admin'] = new_admin_username
                    print("New Admin:", new_admin_username, "| Group:", groupname)
                    client.send(b"Your adminship is now transferred to the specified user.")
                else:
                    client.send(b"The user is not a member of this group.")
            else:
                client.send(b"You're not an admin.")
        elif msg == "/whoAdmin":
            client.send(b"/whoAdmin")
            client.recv(1024).decode("utf-8")
            client.send(bytes("Admin: " + groups[groupname]['admin'], "utf-8"))
        elif msg == "/kickMember":
            client.send(b"/kickMember")
            client.recv(1024).decode("utf-8")
            if username == groups[groupname]['admin']:
                client.send(b"/proceed")
                username_to_kick = client.recv(1024).decode("utf-8")
                if username_to_kick in groups[groupname]['all_members']:
                    groups[groupname]['all_members'].remove(username_to_kick)
                    if username_to_kick in groups[groupname]['online_members']:
                        groups[groupname]['clients'][username_to_kick].send(b"/kicked")
                        groups[groupname]['online_members'].remove(username_to_kick)
                        del groups[groupname]['clients'][username_to_kick]
                    print("User Removed:", username_to_kick, "| Group:", groupname)
                    client.send(b"The specified user is removed from the group.")
                else:
                    client.send(b"The user is not a member of this group.")
            else:
                client.send(b"You're not an admin.")
        elif msg == "/fileTransfer":
            client.send(b"/fileTransfer")
            filename = client.recv(1024).decode("utf-8")
            if filename == "~error~":
                continue
            client.send(b"/sendFile")
            remaining = int.from_bytes(client.recv(4),'big')
            f = open(filename,"wb")
            while remaining:
                data = client.recv(min(remaining,4096))
                remaining -= len(data)
                f.write(data)
            f.close()
            print("File received:", filename, "| User:", username, "| Group:", groupname)
            for member in groups[groupname]['online_members']:
                if member != username:
                    member_client = groups[groupname]['clients'][member]
                    member_client.send(b"/receiveFile")
                    with fileTransferCondition:
                        fileTransferCondition.wait()
                    member_client.send(bytes(filename,"utf-8"))
                    with fileTransferCondition:
                        fileTransferCondition.wait()
                    with open(filename,'rb') as f:
                        data = f.read()
                        dataLen = len(data)
                        member_client.send(dataLen.to_bytes(4,'big'))
                        member_client.send(data)
            client.send(bytes(filename + " successfully sent to all online group members.", "utf-8"))
            print("File sent", filename, "| Group: ", groupname)
            os.remove(filename)
        elif msg == "/sendFilename" or msg == "/sendFile":
            with fileTransferCondition:
                fileTransferCondition.notify()
        else:
            print("UNIDENTIFIED COMMAND:", msg)

def handshake(client):
    username = client.recv(1024).decode("utf-8")
    client.send(b"/sendGroupname")
    groupname = client.recv(1024).decode("utf-8")
    if groupname in groups:
        if username in groups[groupname]['all_members']:
            connect_to_group(groupname, username, client)
            client.send(b"/ready")
            print("User Connected:", username, "| Group:", groupname)
        else:
            groups[groupname]['join_requests'].add(username)
            groups[groupname]['wait_clients'][username] = client
            send_message_to_group(groupname, f"{username} has requested to join the group.", "PyconChat")
            client.send(b"/wait")
            print("Join Request:", username, "| Group:", groupname)
        threading.Thread(target=pycon_chat, args=(client, username, groupname,)).start()
    else:
        groups[groupname] = create_group(username, client)
        threading.Thread(target=pycon_chat, args=(client, username, groupname,)).start()
        client.send(b"/adminReady")
        print("New Group:", groupname, "| Admin:", username)

def main():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.bind(("localhost", 55558 ))
    listen_socket.listen(10)
    print("PyconChat Server running")
    while True:
        client, _ = listen_socket.accept()
        threading.Thread(target=handshake, args=(client,)).start()

if __name__ == "__main__":
    main()
