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


def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode('utf-8')
            if not msg:
                print("Conexão encerrada pelo servidor.")
                break
            print(f"\n{msg}")
        except:
            print("Erro ao receber mensagem. Conexão encerrada.")
            break
    sock.close()


def send_messages(sock):
    while True:
        try:
            entrada = input()
            if entrada.lower() == "sair":
                print("Encerrando conexão...")
                sock.close()
                break
            sock.send(entrada.encode('utf-8'))
        except:
            print("Erro ao enviar. Conexão encerrada.")
            break


def main():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 5555))
        print("Conectado ao servidor.")
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return

    threading.Thread(target=receive_messages,
                     args=(client,), daemon=True).start()
    send_messages(client)


if __name__ == "__main__":
    main()
