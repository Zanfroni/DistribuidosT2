import os, sys, socket
import _thread as thread
from time import sleep
import time

# Nao alterar
DEFAULT_PORT = 7000

#Todas estas sao variaveis auxiliares necessarias
proc_id = -1
ip = -1
port = -1
priority_queue = []

unlocked = True
function_with = ""

coordinator = False
coordinator_node = -1
coordinator_ip = -1
coordinator_port = -1

in_election = False
consense_to_send = []
consense_to_recv = -1

count = 1
using = []
blacklisted_nodes = []

# MENSAGENS DE COMUNICACAO
REQUEST = 'REQUEST'
GRANTED = 'GRANTED'
DENIED = 'DENIED'
ON_QUEUE = 'ON_QUEUE'
DONE = 'DONE'
WAIT = 'WAIT'
LEADER_DEAD = 'LEADER_DEAD'
CONSENSE = 'CONSENSE'
IM_LEADER = 'IM_LEADER'
BLACKLISTED = 'BLACKLISTED'

# total_nodes DEVE ter o tamanho da quantidade de nodos no arquivo
total_nodes = 4
other_nodes = {}

# Principal. Da inicio
def main():
    startFile()
    clear()
    launch()
    
    while True:
        sleep(0.1)

# Aqui da inicio.
# Os nodos iram ter 2 funcoes. Uma que escuta outras mensagens, que sera o Hub principal,
# enquanto quem NAO for o coordenador tera uma funcionalidade que pode enviar mensagens
# para usar a secao critica
def launch():
    global proc_id,ip,port, other_nodes
    try:
        proc_id, ip, port = reader(sys.argv[1],sys.argv[2])
        port = int(port)

        # Agora tem que preencher este computador com todos os outros
        fill(sys.argv[1],proc_id)
        startCoordinator()

        # Agora, precisa-se iniciar as escutas deste NODO com as Threads.
        # Se ele é o coordenador, ele simplesmente escuta.
        # Se ele não for, ele pode tanto escutar quando enviar
        if not coordinator:
            thread.start_new_thread(requestSection,())
        thread.start_new_thread(listenToNodes,())

    except:
        print('Erro de execução do algoritmo! Tente Novamente')
        sys.exit()

''' -------------------------------------------------------------------- '''
# AQUI ESTAO PRESENTES AS FUNCOES ENVOLVIDAS NA ELEICAO DO VALENTAO
#
# consensusNodes: Manda mensagem de consenso para os nodos de numero maior, avisando
#   sobre a eleicao
# setConsensus_Send: define quais sao os nodos que ele deve mandar as mensagem de consenso
#   (so os maiores)
# setConsensus_Recv: Define quantas mensagens ele deve receber ate poder atuar (mandar as suas)
#   ex: se 4 inicia a eleicao, 5 espera receber de 4, para entao enviar para 6 e 7. a logica se mantem
# announceLeadership: anuncia para todos que sera o lider
# setLeader: os nodos mudam a informacao para o novo coordenador
# warnNodes: avisa aos nodos que o coordenador MORREU

def consensusNodes():
    global consense_to_send
    for node in consense_to_send:
        TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = proc_id + ':' + CONSENSE
        destination = (node[0],node[1])
        signal = bytes(data,'utf-8')
        TCP_sock.connect(destination)
        TCP_sock.send(signal)
        TCP_sock.close()
    consense_to_send = []
        
def setConsensus_Send():
    for node in other_nodes:
        if int(node) > int(proc_id):
            consense_to_send.append((other_nodes[node][0],other_nodes[node][1]))
    # Se ele nao tem ninguem pra enviar, ele sera o leader
    if len(consense_to_send) == 0:
        announceLeadership()

def setConsensus_Recv(con_node):
    global consense_to_recv
    if int(proc_id) > int(con_node):
        consense_to_recv += 1
    for node in other_nodes:
        if int(node) < int(proc_id) and int(node) > int(con_node):
            consense_to_recv += 1

def announceLeadership():
    global coordinator, in_election
    for node in other_nodes:
        TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = proc_id + ':' + IM_LEADER
        destination = (other_nodes[node][0],other_nodes[node][1])
        signal = bytes(data,'utf-8')
        TCP_sock.connect(destination)
        TCP_sock.send(signal)
        TCP_sock.close()
    coordinator = True
    in_election = False

def setLeader(leader_id):
    global coordinator_ip,coordinator_node,coordinator_port, in_election
    for node in other_nodes:
        if node == leader_id:
            coordinator_node = leader_id
            coordinator_ip = other_nodes[node][0]
            coordinator_port = other_nodes[node][1]
            in_election = False

def warnNodes(message):
    global coordinator_node,coordinator_ip,coordinator_port, in_election
    try:
        other_nodes.pop(coordinator_node)
        coordinator_node,coordinator_ip,coordinator_port = '-1','-1',-1
        for node in other_nodes:
            TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            
            data = proc_id + ':' + message
            destination = (other_nodes[node][0],other_nodes[node][1])
            signal = bytes(data,'utf-8')
            TCP_sock.connect(destination)
            TCP_sock.send(signal)
            TCP_sock.close()
        in_election = True
    except:
        print('Ocorreu algum erro durante a eleicao!!')

''' -------------------------------------------------------------------- '''

# ESTAS FUNCOES DEFINEM AS FUNCOES NORMAIS DO NODO
#
# send_message: envia uma mensagem a um nodo. Se cair no except, significa que o coordenador
#   esta morto e uma eleicao precisa ser iniciada
# blacklistCount: contagem para o "cavalheirismo". Se esgotar, ele bane o nodo
# requestSection: Thread usada SO PARA OS NAO COORDENADORES. Eles digitam WRITE para simplesmente requisitar
#   a secao
# listenToNodes: HUB PRINCIPAL. Aqui ele escuta todas as mensagens e trata de acordo o recebido
#       * REQUEST: coordenador only. Coordenador recebe e da ao nodo a secao
#       * GRANTED: nodo foi permitido a usar a secao
#       * DONE: coordenador only. Sera notificado que o nodo terminou de usar a secao
#       * DENIED: Recusado e posto na fila de prioridades
#       * BLACKLISTED: Nodo foi banido
#       * WAIT: Nodo esta impaciente, precisa esperar
#       * CONSENSE: Mensagem de consenso da eleicao
#       * IM_LEADER: Coordenador anunciado

def send_message(message,id,ip,port):
    try:
        TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = id + ':' + message
        destination = (ip,port)
        signal = bytes(data,'utf-8')
        TCP_sock.connect(destination)
        TCP_sock.send(signal)
        TCP_sock.close()
    except:
        print('COORDENADOR MORTO! INICIANDO UMA NOVA ELEICAO')
        log(id,'STARTED')
        warnNodes(LEADER_DEAD)
        setConsensus_Send()
        consensusNodes()
        TCP_sock.close()

def blacklistCount(node_id):
    global unlocked
    start_time = time.time()
    current_time = time.time()
    while current_time - start_time < 5:
        sleep(0.1)
        current_time = time.time()
    if node_id in using:
        unlocked = True
        using.remove(node_id)
        blacklisted_nodes.append(node_id)
        log(node_id,'BLACKLISTED')

def requestSection():
    while not coordinator:
        #clear()
        print('Digite WRITE se voce quer escrever (acesso a regiao critica)')
        request = input()
        if not in_election:
            if request == 'WRITE':
                print('REQUISITANDO ACESSO AO COORDENADOR...')
                send_message(REQUEST,proc_id,coordinator_ip,coordinator_port)
        else:
            print('Eleicao em andamento. Nao e possivel requisitar secao!!')

def listenToNodes():
    global function_with, unlocked, coordinator_ip,coordinator_node,coordinator_port,in_election,consense_to_recv

    try:
        tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        origin = (ip, port)
        tcp_server.bind(origin)
        tcp_server.listen(10)

        while True:
            try:
                #Verifica se tem algum nodo na fila de prioridades
                if coordinator:
                    if len(priority_queue) > 0 and unlocked:
                        next_node = priority_queue.pop(0)
                        function_with = next_node[0]
                        print(next_node[0])
                        unlocked = False
                        send_message(GRANTED,proc_id,next_node[1],DEFAULT_PORT+int(next_node[0]))
                        using.append(next_node[0])
                        thread.start_new_thread(blacklistCount,(next_node[0],))
                        log(next_node[0],'GRANTED')

                connection, client = tcp_server.accept()
                message = str(connection.recv(1024)).strip('b')[1:-1]
                message_parts = message.split(":")
                node_id = message_parts[0]
                data = message_parts[1]

                # se eu for o coordenador, tenho acesso a mais funcoes
                if coordinator:
                    if data == 'REQUEST':
                        if node_id in blacklisted_nodes:
                            send_message(BLACKLISTED,proc_id,client[0],DEFAULT_PORT+int(node_id))
                            log(node_id,'TRIED')
                        elif unlocked:
                            function_with = node_id
                            unlocked = False
                            send_message(GRANTED,proc_id,client[0],DEFAULT_PORT+int(node_id))
                            thread.start_new_thread(blacklistCount,(node_id,))
                            using.append(node_id)
                            log(node_id,'GRANTED')
                        else:
                            in_queue = False
                            #Verifica se o cara ta na fila
                            for i in priority_queue:
                                if i[0] == node_id:
                                    send_message(WAIT,proc_id,client[0],DEFAULT_PORT+int(node_id))
                                    log(node_id,'IDIOT')
                                    in_queue = True
                            if not in_queue:
                                send_message(DENIED,proc_id,client[0],DEFAULT_PORT+int(node_id))
                                priority_queue.append((node_id,client[0]))
                                log(node_id,'WAIT')
                    if data == 'DONE':
                        if node_id not in blacklisted_nodes:
                            function_with = -1
                            using.remove(node_id)
                            unlocked = True
                            log(node_id,'USED')
                        else:
                            log(node_id,'BANNED')
                if data == 'GRANTED':
                    lock()
                    writingFunction(proc_id)
                    #Este sleep sera apenas para simular o tempo usado
                    sleep(4)
                    unlock()
                    send_message(DONE,proc_id,client[0],DEFAULT_PORT+int(node_id))
                if data == 'DENIED':
                    print('Secao esta sendo utilizada por ' + node_id)
                    print('Voce foi posto na fila de espera')
                if data == 'WAIT':
                    print('Espera um pouco. Python cachorra!')
                if data == 'LEADER_DEAD':
                    print('Lider morto. Eleicao sera iniciada e conduzida por ' + node_id)
                    other_nodes.pop(coordinator_node)
                    coordinator_node,coordinator_ip,coordinator_port = '-1','-1',-1
                    in_election = True
                    setConsensus_Send()
                    setConsensus_Recv(node_id)
                if data == 'CONSENSE':
                    consense_to_recv -= 1
                    if consense_to_recv == 0:
                        if len(consense_to_send) == 0:
                            announceLeadership()
                        else:
                            consensusNodes()
                if data == 'IM_LEADER':
                    setLeader(node_id)
                    log(coordinator_node,'ENDED')
                    in_election = False
                if data == 'BLACKLISTED':
                    print('Voce foi banido do servico pelo lider atual')
            except:
                print('Ocorreu algum problema na conexao')
                connection.close()
    except:
        print('Ocorreu algum problema no servico')
        tcp_server.close()

''' -------------------------------------------------------------------- '''

# Aqui define QUEM sera o coordenador
def startCoordinator():
    global proc_id,coordinator,coordinator_ip,coordinator_node,coordinator_port
    if proc_id == str(total_nodes):
        coordinator = True
        print('SOU O COORDENADOR')
        sleep(1)
    else:
        coordinator_node = str(total_nodes)
        coordinator_ip,coordinator_port = getCoordinatorInfo()
    
''' SECAO CRITICA '''
def writingFunction(node_id):
    global count
    f = open('writing_file.txt','a')
    f.write('Eu, nodo ' + node_id + ' acessei a secao critica, escrevendo pela ' + str(count) + ' vez\n')
    count += 1
    f.close()

# FUNCOES QUE SIMULAM UM lock() E unlock()    
def lock():
    os.rename('writing_file.txt','LOCKED_writing_file.txt')
def unlock():
    os.rename('LOCKED_writing_file.txt','writing_file.txt')

# Simulacao do Log para o coordenador
def log(node_id,info):
    f = open('writing_file.txt','a')
    if info == 'GRANTED':
        print('Nodo ' + node_id + ' comecou a usar a secao critica (escrevendo)')
        f.write('Nodo ' + node_id + ' comecou a usar a secao critica (escrevendo)\n')
    if info == 'USED':
        print('Nodo ' + node_id + ' saiu da secao critica (finalizou)')
        f.write('Nodo ' + node_id + ' saiu da secao critica (finalizou)\n')
    if info == 'WAIT':
        print('Nodo ' + node_id + ' tentou acessar secao critica e foi posto na fila de espera')
        f.write('Nodo ' + node_id + ' tentou acessar secao critica e foi posto na fila de espera\n')
    if info == 'IDIOT':
        print('Nodo ' + node_id + ' esta bastante impaciente!')
        f.write('Nodo ' + node_id + ' esta bastante impaciente!\n')
    if info == 'STARTED':
        print('Eleicao teve inicio, conduzida por ' + node_id)
        f.write('Eleicao teve inicio, conduzida por ' + node_id + '\n')
    if info == 'ENDED':
        print('Eleicao encerrada. Consenso atingido. Novo lider sera ' + node_id)
        f.write('Eleicao encerrada. Consenso atingido. Novo lider sera ' + node_id + '\n')
    if info == 'BLACKLISTED':
        print('Nodo ' + node_id + ' nao se comportou direito e foi banido do sistema!')
        f.write('Nodo ' + node_id + ' nao se comportou direito e foi banido do sistema!\n')
    if info == 'TRIED':
        print('Nodo banido ' + node_id + ' tentou acessar o servico e teve acesso negado!')
        f.write('Nodo banido ' + node_id + ' tentou acessar o servico e teve acesso negado!\n')
    if info == 'BANNED':
        print('Este computador ('+ node_id + ') foi banido de usar o servico')
        f.write('Este computador ('+ node_id + ') foi banido de usar o servico\n')
    f.close()

# Auxiliar. Pega informacoes do coordenador para os nodos saberem quem ele sera
def getCoordinatorInfo():
    global proc_id,other_nodes
    return other_nodes[coordinator_node][0],other_nodes[coordinator_node][1]

#Auxiliar. Preenche a lista de nodos para saber a topologia do sistema
def fill(config_file,proc_id):
    global other_nodes
    with open(config_file,'r') as f:
        line = f.readline()
        while(line):
            line.strip()
            data = line.split(' ')
            if(data[0] != proc_id):
                other_nodes.update( { data[0] : (data[1],int(data[2])) } )
            line = f.readline()
        f.close()

#Auxiliar. Le o arquivo
def reader(config_file, config_line):
    try:
        reading = ""
        with open(config_file,'r') as f:
            line = int(config_line)

            if line == 1:
                reading = f.readline()
            else:
                for i,reading in enumerate(f):
                    if i == line-2:
                        reading = f.readline()
                        break
            f.close()

        data = reading.split(' ')
        proc_id = data[0]

        ip = data[1]
        port = data[2]
        if ip != verifyIp():
            print('Erro. Verificação de IP inválida!')
            sys.exit()
        
        return proc_id,ip,port
    except:
        print('Erro durante leitura do arquivo! Tente Novamente')
        sys.exit()

def verifyIp():
    # Magicamente pega o IP do PC atual
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    real_ip = s.getsockname()[0]
    s.close()
    return real_ip

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
    print('Digite \'quit\' a qualquer instante para sair')
    print('---------------------------------------------')

def startFile():
    if os.path.exists("writing_file.txt"):
        os.remove("writing_file.txt")
    f = open("writing_file.txt","w+")
    f.close()

if __name__ == "__main__":
    main()