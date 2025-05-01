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

import socket
import threading

# Receber mensagens do Servidor


def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode('utf-8')
            if msg:
                print(f"\n{msg}")
        except:
            print("Conexão encerrada pelo servidor.")
            break


def send_messages(sock, username):
    while True:
        msg = input()
        if msg.lower() == "sair":
            print("Encerrando conexão...")
            sock.close()
            break
        full_msg = f"{username}: {msg}"
        try:
            sock.send(full_msg.encode('utf-8'))
        except:
            print("Erro ao enviar mensagem.")
            break


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 5555))

    username = input("Digite seu nome de usuário: ")

    threading.Thread(target=receive_messages,
                     args=(client,), daemon=True).start()  # daemon=true para facilitar saida do programa
    send_messages(client, username)


if __name__ == "__main__":
    main()
