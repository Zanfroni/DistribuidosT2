import shutil, sys, socket
import _thread as thread
from time import sleep

# Magicamente pega o IP do PC atual
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
real_ip = s.getsockname()[0]
s.close()

def main():
    print('Digite \'quit\' a qualquer instante para sair')
    launch()

    sys_quit = ""
    while(sys_quit != 'quit'):
        sys_quit = input()

    print('Programa encerrado!')
    sys.exit()

def launch():
    try:
        proc_id, host, port = reader(sys.argv[1],sys.argv[2])
        print(proc_id)
        print(host)
        print(port)

        # Agora tem que preencher este computador com todos os outros

    except:
        print('Erro de execução do algoritmo! Tente Novamente')
        sys.exit()

def test():
    print('thread done')

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


if __name__ == "__main__":
    main()