import os, sys, socket
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
CONFIRMED = 'CONFIRMED'

total_nodes = 5
other_nodes = {}

def main():
    startFile()
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
        conn, address = TCP_sock.accept()
        print(address)
        data = str(conn.recv(1024)).strip('b')[1:-1]
        print(data)
        message_parts = data.split(":")

        # Aqui tem que ter a mensagem REQUEST regiao critica
        if message_parts[1] == 'REQUEST':
            print('isadjss')
            print('PROCESSO DE ID ' + message_parts[0] + ' PEDIU ACESSO')
            message = GRANTED + ':'
            signal = bytes(message,'utf-8')
            conn.send(signal)

            # APOS DAR GRANT, TEM QUE FAZER O CAVALHEIRISMO (farei uma thread que responde a isso)
            '''elapsed = 0
            start = time.time()
            time.clock()
            while(elapsed <= 5):
                print(time.time())
                elapsed = time.time() - start
                sleep(0.5)
                '''
            data = str(conn.recv(1024)).strip('b')[1:-1]
            print(data)
            message_parts = data.split(":")
            if message_parts[1] == 'DONE':
                print('adsaad')
                message = CONFIRMED + ':'
                signal = bytes(message,'utf-8')
                conn.send(signal)
                conn.close()
                print('Comunicacao com o nodo encerrada...')
                sleep(2)

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

def startFile():
    if os.path.exists("writing_file.txt"):
        os.remove("writing_file.txt")
    f = open("writing_file.txt","w+")
    f.close()

if __name__ == "__main__":
    main()