import os, shutil, sys, socket
import _thread as thread
from time import sleep

proc_id = -1
ip = -1
port = -1
priority_queue = []

coordinator = False
coordinator_node = -1
coordinator_ip = -1
coordinator_port = -1

# Magicamente pega o IP do PC atual
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
real_ip = s.getsockname()[0]
s.close()

# MENSAGENS DE COMUNICACAO
REQUEST = 'REQUEST'
GRANTED = 'GRANTED'
DENIED = 'DENIED'
ON_QUEUE = 'ON_QUEUE'
DONE = 'DONE'

total_nodes = 5
other_nodes = {}

def main():
    clear()
    launch()
    
    sys_quit = ""
    while(sys_quit != 'quit'):
        sys_quit = input()

    print('Programa encerrado!')
    sys.exit()

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
        if coordinator:
            thread.start_new_thread(listenToCitizens,())
        else:
            thread.start_new_thread(requestCriticSection,())
        
        print(other_nodes)
        print(coordinator)

    #except:
        #print('Erro de execução do algoritmo! Tente Novamente')
        #sys.exit()

def requestCriticSection():
    while True:
        clear()
        print('Digite WRITE se voce quer escrever (acesso a regiao critica)')
        request = input()
        if request == 'WRITE':
            clear()
            print('REQUISITANDO ACESSO AO COORDENADOR...')
            sleep(2)
            UNI_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            address = (coordinator_ip,coordinator_port)
            message = REQUEST
            signal = bytes(message,'utf-8')
            UNI_sock.sendto(signal,address)
            # GOOD TO GO HERE

            rawdata,address = UNI_sock.recvfrom(1024)
            data = str(rawdata).strip('b')[1:-1]
            message_parts = data.split(':')
            if message_parts[0] == 'GRANTED':
                print('very noice')
                sleep(1)







def listenToCitizens():

    # Este escuta na PROPRIA porta
    UNI_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UNI_sock.bind(('',port))

    while True:

        rawdata,address = UNI_sock.recvfrom(1024)
        if address != ip:
            data = str(rawdata).strip('b')[1:-1]
            message_parts = data.split(':')
            # Aqui tem que ter a mensagem REQUEST regiao critica
            if message_parts[0] == 'REQUEST':
                print('isadjss')
                signal = bytes(GRANTED,'utf-8')
                UNI_sock.sendto(signal,address)

            if message_parts[0] == 'DONE':
                print('adsaad')


def startCoordinator():
    global proc_id,coordinator,coordinator_ip,coordinator_node,coordinator_port
    if proc_id == str(total_nodes):
        coordinator = True
        print('VOCE VIROU O COORDENADOR!')
    else:
        coordinator_node = str(total_nodes)
        coordinator_ip,coordinator_port = getCoordinatorInfo()
    # inacabado
    # tem que definir as outras funcoes do coordenador
    
def writingFunction():
    print('escrevi alguma coisa aqui')


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
        if ip != real_ip:
            print('Erro. Verificação de IP inválida!')
            sys.exit()
        
        return proc_id,ip,port
    except:
        print('Erro durante leitura do arquivo! Tente Novamente')
        sys.exit()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
    print('Digite \'quit\' a qualquer instante para sair')
    print('---------------------------------------------')

if __name__ == "__main__":
    main()