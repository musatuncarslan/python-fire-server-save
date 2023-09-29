from connection import Connection
from saveData import SaveData
import socket
import logging
import multiprocessing

class Server:
    """
    Something something docstring.
    """

    def __init__(self, address, port, savedatafolder):
        logging.info("Starting server and listening for data at %s:%d", address, port)

        if (multiprocessing is True):
            logging.debug("Multiprocessing is enabled.")

        self.savedatafolder = savedatafolder
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((address, port))

    def serve(self):
        logging.debug("Serving... ")
        self.socket.listen(0)

        while True:
            sock, (remote_addr, remote_port) = self.socket.accept()

            logging.info("\tAccepting connection from: %s:%d", remote_addr, remote_port)
            self.handle(sock)

    def handle(self, sock):
        try:
            connection = Connection(sock)
            saveData = SaveData(connection, self.savedatafolder)
            for item in saveData:
                hf = item
        except Exception as e:
            logging.exception(e)
        finally:
            # Encapsulate shutdown in a try block because the socket may have
            # already been closed on the other side
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            sock.close()
            logging.info("\tSocket closed")
            # Dataset may not be closed properly if a close message is not received
            if hf:
                try:
                    hf.close()
                    logging.info("\tIncoming data was saved at %s", self.savedatafolder)
                    #oldext = os.path.splitext()[1]
                    #os.rename(file, file+ metadata.measurementInformation.measurementID + oldext)
                except Exception as e:
                    logging.exception(e)

