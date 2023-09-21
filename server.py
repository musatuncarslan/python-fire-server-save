from connection import Connection

import socket
import logging
import multiprocessing
import ismrmrd.xsd
import os
import h5py
import time
from datetime import datetime


class Server:
    """
    Something something docstring.
    """

    def __init__(self, address, port, savefolder, savedataFolder, multiprocessing):
        logging.info("Starting server and listening for data at %s:%d", address, port)

        if (multiprocessing is True):
            logging.debug("Multiprocessing is enabled.")

        self.multiprocessing = multiprocessing
        self.savedataFolder = savedataFolder
        self.savefolder = savefolder
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((address, port))
    def serve(self):
        logging.debug("Serving... ")
        self.socket.listen(0)

        while True:
            sock, (remote_addr, remote_port) = self.socket.accept()

            logging.info("Accepting connection from: %s:%d", remote_addr, remote_port)

            if (self.multiprocessing is True):
                process = multiprocessing.Process(target=self.handle, args=[sock])
                process.daemon = True
                process.start()
                logging.debug("Spawned process %d to handle connection.", process.pid)
            else:
                self.handle(sock)

    def handle(self, sock):
        try:

            connection = Connection(sock, self.savefolder, "", self.savedataFolder, "dataset")

            # Iterate over the connection class and get the messages one by one.
            # 1. Message 1 should be the Config File/Message
            # 2. Message 2 should be the XML Metadata
            # 3. Message 3 and onwards should be the image data
            # Received data is saved as byte arrays in a h5 file.
            imageNo = 0
            for item in connection:
                now = datetime.now()
                # Break out if a connection was established but no data was received
                if item is None:
                    logging.info("The connection will be closed since no data has been received")
                    connection.send_close()
                elif item[0] == 1:
                    # First message is the config (file or text)
                    config_message, config, config_bytes = item
                elif item[0] == 3:
                    # Second messages is the metadata (text)
                    xml_message, metadata_xml, metadata_bytes = item
                    try:
                        metadata = ismrmrd.xsd.CreateFromDocument(metadata_xml)
                        if metadata.acquisitionSystemInformation.systemFieldStrength_T is not None:
                            logging.info("\tData is from a %s %s at %1.1fT",
                                         metadata.acquisitionSystemInformation.systemVendor,
                                         metadata.acquisitionSystemInformation.systemModel,
                                         metadata.acquisitionSystemInformation.systemFieldStrength_T)
                            if self.savedataFolder:
                                hf = h5py.File(self.savedataFolder + '/measurement-' + now.strftime("%Y%m%dT%H%M%S") + '.hdf5', 'w')
                                while not os.path.exists(self.savedataFolder + '/measurement-' + now.strftime("%Y%m%dT%H%M%S") + '.hdf5'):
                                    time.sleep(0.1)
                                    logging.info("Waiting for file...")
                            hf.create_dataset("Config File", data=bytearray(config_bytes))
                            hf.create_dataset("Metada XML", data=bytearray(metadata_bytes))
                    except:
                        logging.warning("Metadata is not a valid MRD XML structure.  Passing on metadata as text")
                elif item[0] == 1022:
                    logging.info("\tIncoming dataset contains %d encoding(s)", len(metadata.encoding))
                    logging.info(
                        "\tEncoding type: '%s', FOV: (%s x %s x %s)mm^3, Matrix Size: (%s x %s x %s)",
                        metadata.encoding[0].trajectory,
                        metadata.encoding[0].encodedSpace.matrixSize.x,
                        metadata.encoding[0].encodedSpace.matrixSize.y,
                        metadata.encoding[0].encodedSpace.matrixSize.z,
                        metadata.encoding[0].encodedSpace.fieldOfView_mm.x,
                        metadata.encoding[0].encodedSpace.fieldOfView_mm.y,
                        metadata.encoding[0].encodedSpace.fieldOfView_mm.z)

                    image_message, item, header_bytes, attribute_bytes, data_bytes = item
                    hf.create_dataset("image_" + str(imageNo) + "/header", data=bytearray(header_bytes))
                    hf.create_dataset("image_" + str(imageNo) + "/attribute", data=bytearray(attribute_bytes))
                    hf.create_dataset("image_" + str(imageNo) + "/data", data=bytearray(data_bytes))
                    imageNo += 1
                else:
                    connection.send_close()
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
            logging.info("Socket closed")

            # Dataset may not be closed properly if a close message is not received
            if hf:
                try:
                    hf.close()
                    logging.info("Incoming data was saved at %s", self.savedataFolder)
                    #oldext = os.path.splitext()[1]
                    #os.rename(file, file+ metadata.measurementInformation.measurementID + oldext)
                except Exception as e:
                    logging.exception(e)

