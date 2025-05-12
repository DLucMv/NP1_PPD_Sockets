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


import tkinter as tk
from tkinter import messagebox
import socket
import threading


cliente = None  # Socket do cliente, usado globalmente
fase_jogo = 1  # Começa o jogo na Fase 1
destino = None
origem_selecionada = None


# Melhoria de UX
def bloquear_tabuleiro(ativo):
    estado = tk.NORMAL if ativo else tk.DISABLED
    for linha in tabuleiro:
        for botao in linha:
            botao.config(state=estado)

# Função para iniciar a conexão com o servidor


def conectar_servidor():
    global cliente
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect(("localhost", 5555))
        messagebox.showinfo(
            "Conectado", "Conexão estabelecida com o servidor!")
        return cliente
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao conectar: {e}")
        return None

# Função para receber mensagens do servidor e exibir na interface gráfica


def receber_mensagens(cliente):
    global fase_jogo
    while True:
        try:
            msg = cliente.recv(1024).decode('utf-8')
            if not msg:
                print("Conexão encerrada pelo servidor.")
                break
            # Atualiza a área de mensagens com a nova mensagem
            adicionar_mensagem(msg)
            if "FASE2" in msg:
                fase_jogo = 2
                adicionar_mensagem(
                    "Início da Fase 2 - Selecione origem e destino.")
        except:
            print("Erro ao receber mensagem. Conexão encerrada.")
            break


# Botão conectar
def conectar():
    global cliente
    cliente = conectar_servidor()
    if cliente:
        threading.Thread(target=receber_mensagens,
                         args=(cliente,), daemon=True).start()
        entry_mensagem.config(state=tk.NORMAL)
        btn_enviar.config(state=tk.NORMAL)
        btn_sair.config(state=tk.NORMAL)
        bloquear_tabuleiro(True)


# Botão sair/desistir
def sair():
    global cliente
    try:
        if cliente:
            cliente.send("SAIR".encode('utf-8'))
            cliente.close()
            cliente = None
            adicionar_mensagem("Você saiu do jogo.")
    except:
        adicionar_mensagem("Erro ao sair ou conexão já encerrada.")
    finally:
        btn_sair.config(state=tk.DISABLED)
        btn_enviar.config(state=tk.DISABLED)
        entry_mensagem.config(state=tk.DISABLED)
        root.quit()

# Função para adicionar mensagens no campo de texto


def adicionar_mensagem(msg):
    chat_area.config(state=tk.NORMAL)  # Permite editar a área de texto
    chat_area.insert(tk.END, msg + "\n")  # Adiciona a mensagem ao final
    chat_area.config(state=tk.DISABLED)  # Desabilita a edição da área de texto
    chat_area.yview(tk.END)  # Faz o scroll para a última mensagem


# Enviar jogada para o servidor
def clicar_botao(i, j):
    global cliente, origem_selecionada, fase_jogo
    if not cliente:
        adicionar_mensagem("Conecte-se ao servidor primeiro.")
        return

    if fase_jogo == 1:
        jogada = f"{i} {j}"
        if tabuleiro_estado[i][j] != 0:
            adicionar_mensagem("Esta célula já está ocupada.")
            return
        try:
            cliente.send(jogada.encode('utf-8'))
            adicionar_mensagem(f"Você colocou uma peça em ({i}, {j})")
        except:
            adicionar_mensagem("Erro ao enviar jogada.")
    elif fase_jogo == 2:
        if origem_selecionada is None:
            origem_selecionada = (i, j)
            tabuleiro[i][j].config(bg="yellow")
            adicionar_mensagem(f"Origem selecionada: ({i}, {j})")
        else:
            destino = (i, j)
            tabuleiro[i][j].config(bg="lightgreen")
            jogada = f"{origem_selecionada[0]} {origem_selecionada[1]} {destino[0]} {destino[1]}"
            try:
                cliente.send(jogada.encode('utf-8'))
                adicionar_mensagem(
                    f"Jogada enviada: {origem_selecionada} → {destino}")
            except:
                adicionar_mensagem("Erro ao enviar jogada.")
            finally:
                for linha in tabuleiro:
                    for botao in linha:
                        botao.config(bg="SystemButtonFace")
                origem_selecionada = None
                destino = None
                atualizar_tabuleiro()


# Enviar mensagem de chat pela interface
def enviar_mensagem_interface():
    global cliente
    msg = entry_mensagem.get()
    if msg.strip() == "":
        return
    try:
        cliente.send(f"/chat {msg}".encode('utf-8'))
        adicionar_mensagem(f"Você: {msg}")
        entry_mensagem.delete(0, tk.END)
    except:
        adicionar_mensagem("Erro ao enviar mensagem.")


# Criando o tabuleiro de 5x5
tabuleiro_estado = [[0]*5 for _ in range(5)]  # 0 = vazio, 1 = X, 2 = O
tabuleiro = []


# Função para atualizar o tabuleiro
def atualizar_tabuleiro():
    for i in range(5):  # Considerando um tabuleiro 5x5
        for j in range(5):
            botao = tabuleiro[i][j]
            if tabuleiro_estado[i][j] == 1:
                botao.config(text="X", state=tk.DISABLED,
                             bg="SystemButtonFace")
            elif tabuleiro_estado[i][j] == 2:
                botao.config(text="O", state=tk.DISABLED,
                             bg="SystemButtonFace")
            else:
                botao.config(text=f"{i},{j}",
                             state=tk.NORMAL, bg="SystemButtonFace")


def criar_tabuleiro():
    for i in range(5):
        linha = []
        for j in range(5):
            botao = tk.Button(tabuleiro_frame, width=5, height=2,
                              command=lambda i=i, j=j: clicar_botao(i, j))
            botao.grid(row=i, column=j, padx=5, pady=5)
            linha.append(botao)
        tabuleiro.append(linha)
    atualizar_tabuleiro()
    bloquear_tabuleiro(False)


# Janela principal
root = tk.Tk()
root.title("Jogador Seega")
root.geometry("450x700")

# Área de chat
chat_frame = tk.Frame(root)
chat_frame.pack(pady=10)

chat_area = tk.Text(chat_frame, width=50, height=20, state=tk.DISABLED)
chat_area.pack(padx=10, pady=(10, 5))

entry_mensagem = tk.Entry(chat_frame, width=50, state=tk.DISABLED)
entry_mensagem.pack(side=tk.LEFT, padx=(10, 5))
entry_mensagem.bind("<Return>", lambda e: enviar_mensagem_interface())

btn_enviar = tk.Button(chat_frame, text="Enviar",
                       state=tk.DISABLED, command=enviar_mensagem_interface)
btn_enviar.pack(side=tk.LEFT)

# Botões principais
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

btn_conectar = tk.Button(
    btn_frame, text="Conectar ao Servidor", command=conectar, width=20)
btn_conectar.grid(row=0, column=0, padx=10)

btn_sair = tk.Button(btn_frame, text="Sair / Desistir",
                     command=sair, width=20, state=tk.DISABLED)
btn_sair.grid(row=0, column=1, padx=10)

# Frame para o tabuleiro
tabuleiro_frame = tk.Frame(root)
tabuleiro_frame.pack(pady=10)

# Criar o tabuleiro
criar_tabuleiro()

root.mainloop()
