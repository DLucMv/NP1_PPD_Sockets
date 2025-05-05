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
import random

# Tabuleiro
BOARD_SIZE = 5
EMPTY = '.'
PLAYER_SYMBOLS = ['X', 'O']

# Estado Global para o jogo
clients = []
client_names = {}
pecas_restantes = {PLAYER_SYMBOLS[0]: 12, PLAYER_SYMBOLS[1]: 12}
jogador_atual = 0  # índice no PLAYER_SYMBOLS
tabuleiro = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
jogo_encerrado = False


# Logger
def log_evento(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    with open("log_servidor.txt", "a") as log:
        log.write(f"{timestamp} {msg}\n")


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


def contar_pecas():
    contagem = {PLAYER_SYMBOLS[0]: 0, PLAYER_SYMBOLS[1]: 0}
    for linha in tabuleiro:
        for celula in linha:
            if celula in contagem:
                contagem[celula] += 1
    return contagem


def movimento_valido(x1, y1, x2, y2, jogador):
    # Movimento ortogonal de 1 casa para espaço vazio
    if not all(0 <= val < BOARD_SIZE for val in (x1, y1, x2, y2)):
        return False
    if tabuleiro[x1][y1] != jogador or tabuleiro[x2][y2] != EMPTY:
        return False
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)


def verificar_capturas(jogador, x, y):
    inimigo = PLAYER_SYMBOLS[(PLAYER_SYMBOLS.index(jogador) + 1) % 2]
    direcoes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    capturas_feitas = []

    for dx, dy in direcoes:
        nx, ny = x + dx, y + dy
        cx, cy = x + 2 * dx, y + 2 * dy

        if (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and
                0 <= cx < BOARD_SIZE and 0 <= cy < BOARD_SIZE):
            if tabuleiro[nx][ny] == inimigo and tabuleiro[cx][cy] == jogador:
                capturas_feitas.append((nx, ny))

    for nx, ny in capturas_feitas:
        tabuleiro[nx][ny] = EMPTY
        msg = f"Jogador {jogador} capturou peça em {nx},{ny}\n"
        broadcast(msg.encode())
        log_evento(msg.strip())

    if capturas_feitas:
        contagem = contar_pecas()
        placar = f"Placar: {PLAYER_SYMBOLS[0]}={contagem[PLAYER_SYMBOLS[0]]} | {PLAYER_SYMBOLS[1]}={contagem[PLAYER_SYMBOLS[1]]}\n"
        broadcast(placar.encode())


def tem_movimentos_possiveis(simbolo):
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            if tabuleiro[x][y] != simbolo:
                continue
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if tabuleiro[nx][ny] == EMPTY:
                        return True
    return False


def broadcast(msg):
    for c in clients:
        try:
            c.send(msg)
        except:
            pass


def remove_client(client):
    if client in clients:
        index = clients.index(client)
        simbolo_desistente = PLAYER_SYMBOLS[index]
        simbolo_vencedor = PLAYER_SYMBOLS[(index + 1) % 2]
        clients.remove(client)
        client.close()
        print(
            f"Jogador {simbolo_desistente} desistiu. Vitória de {simbolo_vencedor}")
        log_evento(
            f"Jogador {simbolo_desistente} desistiu. Vitória de {simbolo_vencedor}")
        broadcast(
            f"Jogador {simbolo_desistente} desistiu. Jogador {simbolo_vencedor} venceu por desistência!\n".encode())


def handle_client(conn, player_index):
    global jogador_atual
    simbolo = PLAYER_SYMBOLS[player_index]
    conn.send(f"Você é o jogador {simbolo}\n".encode())
    log_evento(f"Jogador {simbolo} conectado.")

    try:
        # Fase 1: colocação
        while pecas_restantes[PLAYER_SYMBOLS[0]] > 0 or pecas_restantes[PLAYER_SYMBOLS[1]] > 0:
            if jogador_atual != player_index:
                time.sleep(0.1)
                continue

            conn.send("Sua vez! Digite: linha coluna (ou /chat msg):\n".encode())
            msg = conn.recv(1024).decode().strip()

            if not msg:
                remove_client(conn)
                return

            if msg.startswith("/chat "):
                broadcast(f"[Chat de {simbolo}]: {msg[6:]}\n".encode())
                continue

            try:
                x, y = map(int, msg.split())
                if not posicao_valida(x, y):
                    conn.send("Posição inválida. Tente novamente.\n".encode())
                    continue
            except:
                conn.send("Entrada inválida. Use: linha coluna\n".encode())
                continue

            tabuleiro[x][y] = simbolo
            pecas_restantes[simbolo] -= 1
            broadcast(
                f"\nJogador {simbolo} colocou em {x},{y}\n{imprimir_tabuleiro()}\n".encode())
            log_evento(f"Jogador {simbolo} colocou em {x},{y}")
            jogador_atual = (jogador_atual + 1) % 2

        conn.send("Fase 1 encerrada. Aguarde...\n".encode())
        log_evento(f"Jogador {simbolo} terminou Fase 1")

        # Fase 2: movimento e captura
        while True:
            if jogador_atual != player_index:
                time.sleep(0.1)
                continue

            if not tem_movimentos_possiveis(simbolo):
                broadcast(
                    f"Jogador {simbolo} não tem movimentos disponíveis. Fim de jogo!\n".encode())
                log_evento(
                    f"Jogador {simbolo} não tinha movimentos possíveis. Fim de jogo.")
                jogador_oponente = PLAYER_SYMBOLS[(
                    PLAYER_SYMBOLS.index(simbolo) + 1) % 2]
                broadcast(f"Jogador {jogador_oponente} venceu!\n".encode())
                log_evento(f"Fim de jogo. Vencedor: {jogador_oponente}")
                break

            conn.send("Sua vez! Digite: x1 y1 x2 y2 (ou /chat msg):\n".encode())
            msg = conn.recv(1024).decode().strip()

            if not msg:
                remove_client(conn)
                jogo_encerrado = True
                return

            if msg.startswith("/chat "):
                broadcast(f"[Chat de {simbolo}]: {msg[6:]}\n".encode())
                continue

            try:
                x1, y1, x2, y2 = map(int, msg.split())
                if not movimento_valido(x1, y1, x2, y2, simbolo):
                    conn.send("Movimento inválido. Tente novamente.\n".encode())
                    continue
            except:
                conn.send("Entrada inválida. Use: x1 y1 x2 y2\n".encode())
                continue

            tabuleiro[x1][y1] = EMPTY
            tabuleiro[x2][y2] = simbolo
            verificar_capturas(simbolo, x2, y2)
            broadcast(
                f"\nJogador {simbolo} moveu de {x1},{y1} para {x2},{y2}\n{imprimir_tabuleiro()}\n".encode())
            log_evento(f"Jogador {simbolo} moveu de {x1},{y1} para {x2},{y2}")

            contagem = contar_pecas()
            if contagem[PLAYER_SYMBOLS[0]] == 1 or contagem[PLAYER_SYMBOLS[1]] == 1:
                vencedor = PLAYER_SYMBOLS[0] if contagem[PLAYER_SYMBOLS[0]
                                                         ] > contagem[PLAYER_SYMBOLS[1]] else PLAYER_SYMBOLS[1]
                broadcast(
                    f"Fim de jogo! Jogador {vencedor} venceu!\n".encode())
                log_evento(f"Fim de jogo. Vencedor: {vencedor}")
                break

            jogador_atual = (jogador_atual + 1) % 2

        for c in clients:
            try:
                c.send("Jogo encerrado. Conexão será fechada.\n".encode())
                c.close()
            except:
                pass
        clients.clear()
        jogo_encerrado = True
        log_evento("Conexões encerradas e jogo finalizado.")
        return

    except Exception as e:
        log_evento(f"[ERRO] Jogador {simbolo}: {e}")
        remove_client(conn)


def start_server(host="localhost", port=5555):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[SERVIDOR INICIADO] Aguardando conexões em {host}:{port}...")
    log_evento(f"Servidor iniciado em {host}:{port}")

    while len(clients) < 2:
        conn, _ = server.accept()
        clients.append(conn)
        index = len(clients) - 1
        print(f"[CONECTADO] Jogador {PLAYER_SYMBOLS[index]} conectado.")
        log_evento(f"[CONECTADO] Jogador {PLAYER_SYMBOLS[index]}")
        threading.Thread(target=handle_client, args=(conn, index)).start()

    # Aguarda até que todas as peças tenham sido colocadas
    while pecas_restantes[PLAYER_SYMBOLS[0]] > 0 or pecas_restantes[PLAYER_SYMBOLS[1]] > 0:
        time.sleep(0.1)


if __name__ == "__main__":
    start_server()
