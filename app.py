import os, shutil, sys, socket
import _thread as thread
from time import sleep

proc_id = -1
ip = -1
port = -1
coordinator = False

# Magicamente pega o IP do PC atual
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
real_ip = s.getsockname()[0]
s.close()

total_nodes = 3
other_nodes = {}

def main():
    clear()
    launch()

    print('Digite \'quit\' a qualquer instante para sair')
    sys_quit = ""
    while(sys_quit != 'quit'):
        sys_quit = input()

    print('Programa encerrado!')
    sys.exit()

def launch():
        global proc_id,ip,port
    #try:
        proc_id, ip, port = reader(sys.argv[1],sys.argv[2])
        print(proc_id)
        print(ip)
        print(port)

        # Agora tem que preencher este computador com todos os outros
        fill(sys.argv[1],proc_id)
        startCoordinator()

        # Agora, precisa-se iniciar as escutas deste NODO com as Threads.
        # Se ele é o coordenador, ele simplesmente escuta.
        # Se ele não for, ele pode tanto escutar quando enviar
        if coordinator:
            thread.start_new_thread(listenToCitizens(),())
        
        print(other_nodes)
        print(coordinator)

    #except:
        #print('Erro de execução do algoritmo! Tente Novamente')
        sys.exit()

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


def startCoordinator():
    global proc_id,coordinator
    if proc_id == str(total_nodes):
        coordinator = True
    

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

if __name__ == "__main__":
    main()