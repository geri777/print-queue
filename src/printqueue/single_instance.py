from __future__ import annotations

import json
from collections.abc import Iterable

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    paths_received = Signal(list)

    def __init__(self, server_name: str = "org.printqueue.PrintQueue") -> None:
        super().__init__()
        self.server_name = server_name
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        self.server.newConnection.connect(self._accept_connections)
        self._clients: set[QLocalSocket] = set()

    def start_or_forward(self, paths: Iterable[str]) -> bool:
        payload = list(paths)
        if self._forward(payload):
            return False
        if self.server.listen(self.server_name):
            return True
        # A second process may have started listening between our first probe and listen().
        if self._forward(payload):
            return False
        # At this point the endpoint is stale rather than owned by a reachable process.
        QLocalServer.removeServer(self.server_name)
        if self.server.listen(self.server_name):
            return True
        raise RuntimeError(
            f"Einzelinstanz konnte nicht gestartet werden: {self.server.errorString()}"
        )

    def _forward(self, paths: list[str]) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(300):
            return False
        socket.write(json.dumps(paths).encode("utf-8") + b"\n")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return True

    def _accept_connections(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if socket is None:
                continue
            self._clients.add(socket)
            socket.readyRead.connect(lambda client=socket: self._read(client))
            socket.disconnected.connect(lambda client=socket: self._clients.discard(client))
            self._read(socket)

    def _read(self, socket: QLocalSocket) -> None:
        while socket.canReadLine():
            try:
                paths = json.loads(bytes(socket.readLine()).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(paths, list) and all(isinstance(path, str) for path in paths):
                self.paths_received.emit(paths)
