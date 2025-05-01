# UNIVERSIDADE: INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DO CEARÁ (IFCE) - CAMPUS FORTALEZA
# DEPARTAMENTO DE TELEINFORMÁTICA
# CURSO: ENGENHARIA DA COMPUTAÇÃO
# DATA: 05/05/2025
# ALUNO: Davison Lucas Mendes Viana
#
# 1) Objetivo: Implementar o jogo Seega usando sockets
# 2) Funcionalidades Básicas
# * Controle de turno, com definição de quem inicia a partida
# * Movimentação das peças nos tabuleiros
# * Desistência
# * Chat para comunicação durante toda a partida
# * Indicação de vencedor


# Importação das bibliotecas
import socket
import threading
import time


# Configurações do servidor
# HOST = '127.0.0.1'
# PORT = 2244
clients = [2]


def handle_client(conn, addr):
    print(f"[NOVA CONEXÃO] {addr} conectado.")
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break
            broadcast(msg, conn)
        except:
            break
    remove_client(conn)


def broadcast(msg, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.send(msg)
            except:
                remove_client(client)


def remove_client(client):
    if client in clients:
        clients.remove(client)
        client.close()
        print(f"[DESCONECTADO] Um cliente foi removido.")


def start_server(host="localhost", port=5555):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[SERVIDOR INICIADO] Aguardando conexões em {host}:{port}...")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    start_server()
