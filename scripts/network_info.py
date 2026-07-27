import socket

def lan_ip():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8',80))
        return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'
    finally:
        s.close()

if __name__=='__main__':
    ip=lan_ip()
    print('IncendiosNews V3')
    print('Este ordenador: http://127.0.0.1:8765')
    if ip and not ip.startswith('127.'):
        print(f'Móvil/tablet en la misma Wi-Fi: http://{ip}:8765')
    print('Mantén esta ventana abierta para conservar el cron y la actualización automática.')
