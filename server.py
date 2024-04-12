import socket, threading, ssl, pickle, os, dotenv

try:
    open('messages.bin', 'rb').close()
except:
    open('messages.bin', 'wb').close()

dotenv.load_dotenv()

HOST = os.getenv('IP_ADDR', 'localhost')
PORT = int(os.getenv('PORT', '5555'))
CERT_FILE = os.getenv('CERT_FILE', None)
KEY_FILE = os.getenv('KEY_FILE', None)

if (not CERT_FILE or not KEY_FILE):
    print("Required SSL Key and Certificate files not found.")
    exit(1)

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
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
            data = client_socket.recv(20480)
            data = pickle.loads(data)
            if 'message' in data:
                if data['message']!='':
                    loaded_messages[data['room']]['message']=data['message']
                    loaded_messages[data['room']]['logs'].append(data['logs'])
                    clients[data['room']]['message']=data['message']
                    clients[data['room']]['logs'].append(data['logs'])
                    for c in clients[data['room']]['clients']:
                        if c != client_socket:
                            c.send(pickle.dumps(data))
                else:
                    for i in clients[data['room']]['clients']:
                        if i != conn_ssl:
                            i.send(pickle.dumps({'logs':data['logs'], 'message':loaded_messages[data['room']]['message']}))
                    loaded_messages[data['room']]['logs'].append(data['logs'])
                    clients[data['room']]['clients'].remove(client_socket)
                    clients[data['room']]['users'].remove(data['username'])
                    if clients[data['room']]['clients']==[]:
                        clients.pop(data['room'])
                    client_socket.close()
                    return
            elif 'logs' in data:
                print(f"Sending logs to {address} in room {data['room']}")
                conn_ssl.send(pickle.dumps({'logs':loaded_messages[data['room']]['logs']}))
            elif 'users' in data:
                conn_ssl.send(pickle.dumps({'users':clients[data['room']]['users']}))
        except Exception as e:
            print(f"Error: {e}")
            try:
                for i in clients[data['room']]['clients']:
                    if i != conn_ssl:
                        i.send(pickle.dumps({'logs':data['logs'], 'message':loaded_messages[data['room']]['message']}))
                clients[data['room']]['clients'].remove(client_socket)
                clients[data['room']]['users'].remove(data['username'])
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
    data = conn_ssl.recv(20480)
    data = pickle.loads(data)
    if data['room'] in clients and data['username'] in clients[data['room']]['users']:
        conn_ssl.send(pickle.dumps({'error':'username exists'}))
        data=conn_ssl.recv(20480)
        conn_ssl.close()
        continue
    if data['room'] in clients:
        clients[data['room']]['clients'].append(conn_ssl)
        clients[data['room']]['users'].append(data['username'])
        clients[data['room']]['logs'].append(data['logs'])
    else:
        if data['room'] in loaded_messages:
            loaded_messages[data['room']]['logs'].append(data['logs'])
            clients[data['room']] = {'clients':[conn_ssl], 'message':loaded_messages[data['room']]['message'], 'logs':loaded_messages[data['room']]['logs'], 'users':[data['username']]}
            conn_ssl.send(pickle.dumps({'message':loaded_messages[data['room']]['message'], 'logs':data['logs']}))
        else:
            clients[data['room']] = {'clients':[conn_ssl], 'message':None, 'logs':[data['logs']], 'users':[data['username']]}
            loaded_messages[data['room']]={'message':None, 'logs':[data['logs']]}
            conn_ssl.send(pickle.dumps({'message':None}))
    for i in clients[data['room']]['clients']:
        if i != conn_ssl:
            i.send(pickle.dumps({'logs':data['logs'], 'message':loaded_messages[data['room']]['message']}))
    del data
    client_thread = threading.Thread(target=handle_client, args=(conn_ssl, address), daemon=True)
    client_thread.start()
