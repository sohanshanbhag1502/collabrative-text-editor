import socket, threading, ssl, pickle

try:
    file=open('messages.bin', 'rb').close()
except:
    file=open('messages.bin', 'wb').close()

HOST = '10.0.0.4'
PORT = 5555

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile="domain.crt", keyfile="domain.key")
clients = {}
try:
    file=open('messages.bin', 'rb')
    loaded_messages=pickle.load(file)
    file.close()
except:
    loaded_messages={}

# Function to handle client connections
def handle_client(client_socket, address):
    while True:
        try:
            data = client_socket.recv(1024)
            data = pickle.loads(data)
            if data['message']!='':
                loaded_messages[data['room']]=data['message']
                for c in clients[data['room']]['clients']:
                    if c != client_socket:
                        c.send(pickle.dumps([data['message']]))
            else:
                clients[data['room']]['clients'].remove(client_socket)
                if clients[data['room']]==[]:
                    clients.pop(data['room'])
                client_socket.close()
        except Exception as e:
            print(f"Error: {e}")
            try:
                clients[data['room']]['clients'].remove(client_socket)
                if clients[data['room']]==[]:
                    clients.pop(data['room'])
                client_socket.close()
            except:
                pass
            return


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"Server listening on {HOST}:{PORT}")
while True:
    try:
        client_socket, address = server_socket.accept()
    except:
        exit()
    finally:
        file=open('messages.bin', 'wb')
        pickle.dump(loaded_messages, file)
        file.close()
    conn_ssl = ssl_context.wrap_socket(client_socket, server_side=True)
    data = conn_ssl.recv(1024)
    data = pickle.loads(data)
    if data['room'] in clients:
        clients[data['room']]['clients'].append(conn_ssl)
    else:
        clients[data['room']] = {'clients':[conn_ssl], 'message':loaded_messages[data['room']] if data['room'] in loaded_messages else None}
    conn_ssl.send(pickle.dumps([loaded_messages[data['room']]]) if data['room'] in loaded_messages else pickle.dumps([None]))
    client_thread = threading.Thread(target=handle_client, args=(conn_ssl, address), daemon=True)
    client_thread.start()
