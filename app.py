import os, sys, socket
import _thread as thread
from time import sleep

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

total_nodes = 5
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
        TCP_sock.connect(destination)
        TCP_sock.send(signal)
        TCP_sock.close()
    except:
        print('COORDENADOR MORTO! INICIANDO UMA NOVA ELEICAO')
        # Manda mensagem pra todos apagarem os seus coordenadores (os dados), cria um sendtoall() --> dead e sou lider
        # Inicia a eleicao, pegando os node_ids, maiores que os seus. Manda um leader message
        # 

        warnNodes(LEADER_DEAD)
        setConsensus_Send()
        consensusNodes()
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
    data = id + ':' + IM_LEADER

    for node in other_nodes:
        destination = (node[0],node[1])
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
            coordinator_ip = node[0]
            coordinator_port = node[1]
            in_election = False




# TO AVISANDO TODOS OS NODINHOS QUE O COORDENADOR MORREU
# ZERA OS DADOS DELE POIS UMA ELEICAO VAI COMECAR
def warnNodes(message):
    global coordinator_node,coordinator_ip,coordinator_port, in_election
    try:
        TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = id + ':' + message
        for node in other_nodes:
            destination = (node[0],node[1])
            signal = bytes(data,'utf-8')
            TCP_sock.connect(destination)
            TCP_sock.send(signal)
        TCP_sock.close()

        other_nodes.pop(coordinator_node)
        coordinator_node,coordinator_ip,coordinator_port = '-1','-1',-1
        in_election = True
    except:
        print('Ocorreu algum erro durante a eleicao!!')

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

    try:
        tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        origin = (ip, port)
        tcp_server.bind(origin)
        tcp_server.listen(10)

        while True:
            try:

                # ver aqui se tem alguem na fila
                if coordinator:
                    if len(priority_queue) > 0 and unlocked:
                        next_node = priority_queue.pop(0)
                        function_with = next_node[0]
                        unlocked = False
                        send_message(GRANTED,proc_id,next_node[1],DEFAULT_PORT+int(next_node[0]))
                        #log(node_id,)


                connection, client = tcp_server.accept()
                # Mensagem chega na forma de bytes. Precisamos remover o b e as aspas simples
                message = str(connection.recv(1024)).strip('b')[1:-1]
                message_parts = message.split(":")
                node_id = message_parts[0]
                data = message_parts[1]

                # se eu for o coordenador, tenho acesso a mais funcoes
                if coordinator:
                    if data == 'REQUEST':
                        if unlocked:
                            function_with = node_id
                            unlocked = False
                            send_message(GRANTED,proc_id,client[0],DEFAULT_PORT+int(node_id))
                            #log(node_id,)
                        else:
                            in_queue = False
                            #Verifica se o cara ta na fila
                            for i in priority_queue:
                                if i[0] == node_id:
                                    send_message(WAIT,proc_id,client[0],DEFAULT_PORT+int(node_id))
                                    in_queue = True
                            if not in_queue:
                                send_message(DENIED,proc_id,client[0],DEFAULT_PORT+int(node_id))
                                priority_queue.append((node_id,client[0]))
                    if data == 'DONE':
                        function_with = -1
                        unlocked = True
                        print('FOOOOI')
                        #unlog(node_id,)
                if data == 'GRANTED':
                    lock()
                    # WRITING FUNCTION
                    sleep(5)
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



            except Exception as e:
                print('DEU PAU NO CONNECTION CLOSE')
                sleep(1)
                print(e)
                connection.close()
    except:
        print('DEU PAU NO SERVER CLOSE')
        sleep(1)
        tcp_server.close()



def startCoordinator():
    global proc_id,coordinator,coordinator_ip,coordinator_node,coordinator_port
    if proc_id == str(total_nodes):
        coordinator = True
        print('VOCE VIROU O COORDENADOR!')
        sleep(1)
    else:
        coordinator_node = str(total_nodes)
        coordinator_ip,coordinator_port = getCoordinatorInfo()
    # inacabado
    # tem que definir as outras funcoes do coordenador
    
def writingFunction():
    '''if os.path.exists('arquivo.txt'):
            try:
                self.lock()
            except FileNotFoundError:
                return

            with open('lock_arquivo.txt', 'r+') as arquivo:
                last_line = (list(arquivo)[-1])
                last_line = int(last_line)

                operation = "Processo {0} leu o valor {1}{2}".format(self.id_processo, last_line, '\n')
                arquivo.write(operation)
                operation = "Processo {0} adicionou {1}{2}".format(self.id_processo, self.id_processo, '\n')
                arquivo.write(operation)
                last_line = last_line + self.id_processo
                operation = "Processo {0} gravou {1}{2}".format(self.id_processo, last_line, '\n')
                arquivo.write(operation)
                arquivo.write("{0}{1}".format(last_line, '\n'))

            self.unlock()
            self.operacoes_restantes -= 1
        print("{0} operacoes restantes no processo {1}".format(self.operacoes_restantes, self.id_processo))'''
    
def lock():
    os.rename('writing_file.txt','LOCKED_writing_file.txt')
def unlock():
    os.rename('LOCKED_writing_file.txt','writing_file.txt')


def getCoordinatorInfo():
    global proc_id,other_nodes
    return other_nodes[coordinator_node][0],other_nodes[coordinator_node][1]














































'''
def requestCriticSection():
    while True:
        clear()
        print('Digite WRITE se voce quer escrever (acesso a regiao critica)')
        request = input()
        if request == 'WRITE':
            clear()
            print('REQUISITANDO ACESSO AO COORDENADOR...')
            sleep(2)

            TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            destination = (coordinator_ip,coordinator_port)
            TCP_sock.connect(destination)
            message = proc_id + ':' + REQUEST + ':'
            signal = bytes(message,'utf-8')
            address = (coordinator_ip,coordinator_port)
            print(signal)
            TCP_sock.send(signal)
            rawdata,address = TCP_sock.recvfrom(1024)
            data = str(rawdata).strip('b')[1:-1]
            message_parts = data.split(':')
            if message_parts[0] == 'GRANTED':
                print('LOCK GRANTED')
                sleep(1)
                lock()
                # writingFuntion()
                unlock()
                # agora acabei de usar essa cachorra
                print('print cachorra')
                message = proc_id + ':' + DONE + ':'
                signal = bytes(message,'utf-8')
                TCP_sock.send(signal)
                print('aaaa')
                rawdata,address = TCP_sock.recvfrom(1024)
                print('lerina')
                data = str(rawdata).strip('b')[1:-1]
                message_parts = data.split(':')
                if message_parts[0] == 'CONFIRMED':
                    TCP_sock.close()
                    print('Comunicacao com o coordenador encerrada...')
                    sleep(2)







def listenToCitizens():

    # Este escuta na PROPRIA porta (Conexao TCP constante)
    TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    origin = (ip, port)
    TCP_sock.bind(origin)
    TCP_sock.listen(10)

    while True:

        clear()
        conn, client = TCP_sock.accept()
        data = str(conn.recv(1024)).strip('b')[1:-1]
        print(data)
        message_parts = data.split(":")
        client_id = message_parts[0]

        # Aqui tem que ter a mensagem REQUEST regiao critica
        if message_parts[1] == 'REQUEST' and unlocked:
            print('isadjss')
            print('PROCESSO DE ID ' + message_parts[0] + ' PEDIU ACESSO')
            message = GRANTED + ':'
            signal = bytes(message,'utf-8')
            conn.send(signal)
            unlocked = False
        if message_parts[1] == 'DONE':
            print('adsaad')
            unlocked = True
            message = CONFIRMED + ':'
            signal = bytes(message,'utf-8')
            conn.send(signal)
            print('Comunicacao com o nodo encerrada...')
            sleep(2)

            # nesta parte, criar thread que
            # cria uma escuta que
            #
            #

            # APOS DAR GRANT, TEM QUE FAZER O CAVALHEIRISMO (farei uma thread que responde a isso)
            elapsed = 0
            start = time.time()
            time.clock()
            while(elapsed <= 5):
                print(time.time())
                elapsed = time.time() - start
                sleep(0.5)
                '''

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