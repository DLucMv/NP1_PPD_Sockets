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


def fase_2_movimento():
    global jogador_atual
    broadcast("\n--- Fase 2: Movimentação e Captura ---\n".encode())
    log_evento("Início da Fase 2")

    while True:
        jogador = PLAYER_SYMBOLS[jogador_atual]
        cliente = clients[jogador_atual]
        cliente.send(
            "Sua vez! Digite: x1 y1 x2 y2 (mover de -> para):\n".encode())

        try:
            jogada = cliente.recv(1024).decode().strip()

            if not jogada:
                log_evento(
                    f"[DESCONECTADO] Jogador {jogador} enviou mensagem vazia.")
                remove_client(cliente)
                break

            x1, y1, x2, y2 = map(int, jogada.split())

            if not movimento_valido(x1, y1, x2, y2, jogador):
                cliente.send("Movimento inválido. Tente novamente.\n".encode())
                continue

            tabuleiro[x1][y1] = EMPTY
            tabuleiro[x2][y2] = jogador

            verificar_capturas(jogador, x2, y2)

            contagem = contar_pecas()
            tab = imprimir_tabuleiro()
            msg = f"\nJogador {jogador} moveu de {x1},{y1} para {x2},{y2}\n{tab}\n"
            broadcast(msg.encode())
            log_evento(f"{msg.strip()}")

            if contagem[PLAYER_SYMBOLS[0]] == 0 or contagem[PLAYER_SYMBOLS[1]] == 0:
                vencedor = jogador
                broadcast(
                    f"Fim de jogo! Jogador {vencedor} venceu!\n".encode())
                log_evento(f"Fim de jogo. Vencedor: {vencedor}")
                break

            jogador_atual = (jogador_atual + 1) % 2

        except Exception as e:
            log_evento(f"[ERRO FASE 2] Jogador {jogador}: {e}")
            try:
                cliente.send(f"Erro: {e}\n".encode())
            except:
                log_evento(f"[DESCONECTADO] Jogador {jogador} perdeu conexão.")
            remove_client(cliente)
            break  # encerra a fase se o jogador sair


def handle_client(conn, player_index):
    global jogador_atual

    simbolo = PLAYER_SYMBOLS[player_index]
    conn.send(f"Você é o jogador {simbolo}\n".encode())
    log_evento(f"Jogador {simbolo} conectado.")

    try:
        # Fase 1: Colocação de peças
        while True:
            # Sai do loop se ambos os jogadores não tiverem mais peças
            if pecas_restantes[PLAYER_SYMBOLS[0]] == 0 and pecas_restantes[PLAYER_SYMBOLS[1]] == 0:
                break
            # Evitar problemas de corrida
            if jogador_atual != player_index:
                time.sleep(0.1)
                continue

            conn.send("Sua vez! Digite: linha coluna\n".encode())
            data = conn.recv(1024).decode().strip()
            if not data:
                print(f"[DESCONECTADO] Jogador {simbolo}")
                remove_client(conn)
                return

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
            msg = f"\nJogador {simbolo} colocou em {x},{y}\n{tab}\n"
            broadcast(msg.encode())
            log_evento(f"{msg.strip()}")

            jogador_atual = (jogador_atual + 1) % 2

        conn.send(
            "Fase 1 encerrada. Aguarde o início da próxima fase...\n".encode())
        log_evento(f"Jogador {simbolo} terminou Fase 1")

    except Exception as e:
        print(f"[ERRO] Jogador {simbolo}: {e}")
        remove_client(conn)


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
        log_evento("Cliente removido da lista")


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

    # Inicia a Fase 2 após todos colocarem as peças
    fase_2_movimento()


if __name__ == "__main__":
    start_server()
