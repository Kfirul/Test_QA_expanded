from socket import socket, AF_INET, SOCK_STREAM
from typing import Union


def get_current_measurement(port: int,
                            command: Union[bytes, str],
                            host: str = 'localhost',
                            timeout: float = 5.0) -> float:
    """
    Send a measurement command to an ammeter emulator and return the current as a float.

    This is the function the testing framework consumes. The original
    ``request_current_from_ammeter`` only printed the value (returned ``None``),
    which made it impossible to collect samples programmatically.

    Raises:
        ConnectionError: if the emulator returns no data.
        socket.timeout: if the emulator does not respond within ``timeout`` seconds.
        ValueError: if the returned payload is not a valid float.
    """
    if isinstance(command, str):
        command = command.encode('utf-8')

    with socket(AF_INET, SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(command)
        data = s.recv(1024)

    if not data:
        raise ConnectionError(f"No data received from ammeter on port {port}")
    return float(data.decode('utf-8'))


def request_current_from_ammeter(port: int, command: bytes):
    """
    Backwards-compatible helper that prints the measurement (original behaviour),
    now implemented on top of :func:`get_current_measurement`.
    """
    try:
        current = get_current_measurement(port, command)
        print(f"Received current measurement from port {port}: {current} A")
        return current
    except Exception as exc:
        print(f"No data received from port {port}: {exc}")
        return None
