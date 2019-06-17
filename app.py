import os, sys, socket
import _thread as thread
from time import sleep
import time

DEFAULT_PORT = 7000

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

total_nodes = 4
other_nodes = {}

def main():
    startFile()
    clear()
    launch()
    
    while True:
        sleep(0.1)
    '''sys_quit = ""
    while(sys_quit != 'quit'):
        sys_quit = input()

    print('Programa encerrado!')
    sys.exit()'''

def launch():
        global proc_id,ip,port, other_nodes
    #try:
        proc_id, ip, port = reader(sys.argv[1],sys.argv[2])
        port = int(port)
        #print(proc_id)
        #print(ip)
        #print(port)

        # Agora tem que preencher este computador com todos os outros
        fill(sys.argv[1],proc_id)
        startCoordinator()

        # Agora, precisa-se iniciar as escutas deste NODO com as Threads.
        # Se ele é o coordenador, ele simplesmente escuta.
        # Se ele não for, ele pode tanto escutar quando enviar
        if not coordinator:
            thread.start_new_thread(requestSection,())
        thread.start_new_thread(listenToNodes,())
        print(other_nodes)
        print(coordinator)

    #except:
        #print('Erro de execução do algoritmo! Tente Novamente')
        #sys.exit()

def send_message(message,id,ip,port):
    try:
        TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = id + ':' + message
        destination = (ip,port)
        signal = bytes(data,'utf-8')
        print('wtf')
        TCP_sock.connect(destination)
        print('comassim')
        TCP_sock.send(signal)
        TCP_sock.close()
    except:
        TCP_sock.close()
        print('COORDENADOR MORTO! INICIANDO UMA NOVA ELEICAO')
        log(id,'STARTED')
        warnNodes(LEADER_DEAD)
        setConsensus_Send()
        consensusNodes()
        log(coordinator_node,'ENDED')
        TCP_sock.close()

# Aqui eu tenho que mandar mensagem
def consensusNodes():
    global consense_to_send
    TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data = proc_id + ':' + CONSENSE

    for node in consense_to_send:
        destination = (node[0],node[1])
        signal = bytes(data,'utf-8')
        TCP_sock.connect(destination)
        TCP_sock.send(signal)
    consense_to_send = []
    TCP_sock.close()
        
    
def setConsensus_Send():
    for node in other_nodes:
        print(node)
        if int(node) > int(proc_id):
            print('shits good')
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
    TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data = proc_id + ':' + IM_LEADER

    for node in other_nodes:
        destination = (other_nodes[node][0],other_nodes[node][1])
        signal = bytes(data,'utf-8')
        TCP_sock.connect(destination)
        TCP_sock.send(signal)
    TCP_sock.close()
    coordinator = True
    in_election = False
    print('foioooo???')

def setLeader(leader_id):
    global coordinator_ip,coordinator_node,coordinator_port, in_election
    for node in other_nodes:
        if node == leader_id:
            coordinator_node = leader_id
            coordinator_ip = node[0]
            coordinator_port = node[1]
            in_election = False

def warnNodes(message):
    global coordinator_node,coordinator_ip,coordinator_port, in_election
    try:
        TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        other_nodes.pop(coordinator_node)
        coordinator_node,coordinator_ip,coordinator_port = '-1','-1',-1
        data = id + ':' + message
        for node in other_nodes:
            destination = (node[0],node[1])
            signal = bytes(data,'utf-8')
            TCP_sock.connect(destination)
            TCP_sock.send(signal)
        TCP_sock.close()

        in_election = True
    except:
        print('Ocorreu algum erro durante a eleicao!!')

def blacklistCount(node_id):
    global unlocked
    start_time = time.time()
    current_time = time.time()
    while current_time - start_time < 5:
        sleep(0.1)
        current_time = time.time()
    if node_id in using:
        print('DEVERIA TER FEIOT ANTES')
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
                #clear()
                print('REQUISITANDO ACESSO AO COORDENADOR...')
                #sleep(2)
                send_message(REQUEST,proc_id,coordinator_ip,coordinator_port)
        else:
            print('Eleicao em andamento. Nao e possivel requisitar secao!!')

def listenToNodes():
        global function_with, unlocked, coordinator_ip,coordinator_node,coordinator_port,in_election,consense_to_recv

    #try:
        tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        origin = (ip, port)
        tcp_server.bind(origin)
        tcp_server.listen(10)

        while True:
            #try:

                # ver aqui se tem alguem na fila
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
                # Mensagem chega na forma de bytes. Precisamos remover o b e as aspas simples
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
                            print('FOOOOI')
                            log(node_id,'USED')
                        else:
                            log(node_id,'BANNED')
                if data == 'GRANTED':
                    lock()
                    writingFunction(proc_id)
                    sleep(4)
                    unlock()
                    send_message(DONE,proc_id,client[0],DEFAULT_PORT+int(node_id))
                if data == 'DENIED':
                    print('Section is currently being used by ' + node_id)
                    print('Youve been placed in the priority queue. Wait!')
                if data == 'WAIT':
                    print('Wait the fuck, cachorra apressada. Tu ja ta na fila!!!')
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
                if data == 'BLACKLISTED':
                    print('Voce foi banido do servico pelo lider atual')
            #except Exception as e:
                #print('DEU PAU NO CONNECTION CLOSE')
                #sleep(1)
                #print(e)
                #connection.close()
    #except:
        #print('DEU PAU NO SERVER CLOSE')
        #sleep(1)
        #tcp_server.close()


def startCoordinator():
    global proc_id,coordinator,coordinator_ip,coordinator_node,coordinator_port
    if proc_id == str(total_nodes):
        coordinator = True
        print('VOCE VIROU O COORDENADOR!')
        sleep(1)
    else:
        coordinator_node = str(total_nodes)
        coordinator_ip,coordinator_port = getCoordinatorInfo()
    
def writingFunction(node_id):
    global count
    f = open('writing_file.txt','w+')
    f.write('Eu, nodo ' + node_id + ' acessei a secao critica, escrevendo pela ' + str(count) + ' vez')
    count += 1
    f.close()
    
def lock():
    os.rename('writing_file.txt','LOCKED_writing_file.txt')
def unlock():
    os.rename('LOCKED_writing_file.txt','writing_file.txt')

def log(node_id,info):
    f = open('writing_file.txt','w+')
    if info == 'GRANTED':
        print('Nodo ' + node_id + ' comecou a usar a secao critica (escrevendo)')
        f.write('Nodo ' + node_id + ' comecou a usar a secao critica (escrevendo)')
    if info == 'USED':
        print('Nodo ' + node_id + ' saiu da secao critica (finalizou)')
        f.write('Nodo ' + node_id + ' saiu da secao critica (finalizou)')
    if info == 'WAIT':
        print('Nodo ' + node_id + ' tentou acessar secao critica e foi posto na fila de espera')
        f.write('Nodo ' + node_id + ' saiu da secao critica (finalizou)')
    if info == 'IDIOT':
        print('Nodo ' + node_id + ' esta bastante impaciente!')
        f.write('Nodo ' + node_id + ' saiu da secao critica (finalizou)')
    if info == 'STARTED':
        print('Eleicao teve inicio, conduzida por ' + node_id)
        f.write('Eleicao teve inicio, conduzida por ' + node_id)
    if info == 'ENDED':
        print('Eleicao encerrada. Consenso atingido. Novo lider sera ' + node_id)
        f.write('Eleicao encerrada. Consenso atingido. Novo lider sera ' + node_id)
    if info == 'BLACKLISTED':
        print('Nodo ' + node_id + ' nao se comportou direito e foi banido do sistema!')
        f.write('Nodo ' + node_id + ' nao se comportou direito e foi banido do sistema!')
    if info == 'TRIED':
        print('Nodo banido ' + node_id + ' tentou acessar o servico e teve acesso negado!')
        f.write('Nodo banido ' + node_id + ' tentou acessar o servico e teve acesso negado!')
    if info == 'BANNED':
        print('Este computador ('+ node_id + ') foi banido de usar o servico')
        f.write('Este computador foi banido de usar o servico')
    f.close()

def getCoordinatorInfo():
    global proc_id,other_nodes
    return other_nodes[coordinator_node][0],other_nodes[coordinator_node][1]

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