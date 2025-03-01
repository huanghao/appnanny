import socket

PORT_RANGE = list(range(8080, 8090)) + list(range(4040, 4050))


def find_available_port():
    """Find an available port from the configured range"""
    for port in PORT_RANGE:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return None
