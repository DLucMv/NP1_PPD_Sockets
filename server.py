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


BOARD_SIZE = 5
EMPTY = '.'
PLAYER_SYMBOLS = ['X', 'O']
clients = []
client_names = {}
tabuleiro = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
pecas_restantes = {PLAYER_SYMBOLS[0]: 12, PLAYER_SYMBOLS[1]: 12}
jogador_atual = 0  # índice no PLAYER_SYMBOLS


def imprimir_tabuleiro():
    linhas = ["  " + " ".join(str(i) for i in range(BOARD_SIZE))]
    for i, linha in enumerate(tabuleiro):
        linhas.append(f"{i} " + " ".join(linha))
    return "\n".join(linhas)


def posicao_valida(x, y):
    return (
        0 <= x < BOARD_SIZE and
        0 <= y < BOARD_SIZE and
        (x != 2 or y != 2) and
        tabuleiro[x][y] == EMPTY
    )


def handle_client(conn, player_index):
    global jogador_atual

    simbolo = PLAYER_SYMBOLS[player_index]
    conn.send(f"Você é o jogador {simbolo}\n".encode())

    while pecas_restantes[PLAYER_SYMBOLS[0]] > 0 or pecas_restantes[PLAYER_SYMBOLS[1]] > 0:
        if jogador_atual != player_index:
            continue  # espera sua vez

        try:
            conn.send("Sua vez! Digite: linha coluna\n".encode())
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            try:
                x, y = map(int, data.split())
            except ValueError:
                conn.send("Entrada inválida. Use: linha coluna\n".encode())
                continue

            if not posicao_valida(x, y):
                conn.send("Posição inválida. Tente novamente.\n".encode())
                continue

            tabuleiro[x][y] = simbolo
            pecas_restantes[simbolo] -= 1
            tab = imprimir_tabuleiro()
            broadcast(
                f"\nJogador {simbolo} colocou em {x},{y}\n{tab}\n".encode())

            # alterna jogador
            jogador_atual = (jogador_atual + 1) % 2

        except:
            break

    conn.send("Fase 1 encerrada. Aguardando a fase 2...\n".encode())
    conn.close()


def broadcast(msg):
    for c in clients:
        try:
            c.send(msg)
        except:
            pass


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

    while len(clients) < 2:
        conn, addr = server.accept()
        clients.append(conn)
        index = len(clients) - 1
        print(f"[CONECTADO] Jogador {PLAYER_SYMBOLS[index]} conectado.")
        threading.Thread(target=handle_client, args=(conn, index)).start()


if __name__ == "__main__":
    start_server()
