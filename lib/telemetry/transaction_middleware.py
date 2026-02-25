"""
This file will implement the class that will be used by the ground station to deal with the transactions

when the ground station gets a command to create a transaction this class will be called before to create the transaction
when a transaction packet is received this class will also be called and deal with the packet

It will eventually also deal with storing the transaction in storage
    the main idea behind this is to minimize the chances of losing a transaction. it will allow you to recover lost transactions


Storing the transactions in storage is something that takes a bit of time, and I do not want to slow down the receiving 
of data from the Satellite. So there will be a thread that will be responsible for writing thigns to storage and when we receive something we have 
"""

import pickle
import json
from lib.telemetry.splat.splat.transport_layer import TransactionManager, Fragment, Command
import os
import time
import threading
import queue
from scripts.bin_to_png import bin_to_png


class TransactionMiddleware:
    """
    When this module is created, inside the transaction folder it will create a new folder with the timestamp
    this will server as like sessions
    Inside this folder it will create a json file for each of the transactions containing all of the information
        and an associated pickle file that will contain the dict with the fragments received so far
    """
    
    def __init__(self, storage_folder="transactions"):
        self.storage_folder = storage_folder
        self.transaction_manager = TransactionManager()
        
        # check to see if the storage folder exists, if not create it
        if not os.path.exists(self.storage_folder):
            os.makedirs(self.storage_folder)
            
        # create the session folder with the timestamp
        self.session_folder = os.path.join(self.storage_folder, f"session_{int(time.time())}")
        os.makedirs(self.session_folder)

        # queue for dumping transactions to storage in the background
        # each item in the queue is a tuple of (transaction, json_file_path)
        self._dump_queue = queue.Queue()
        self._dump_thread = threading.Thread(target=self._dump_worker, daemon=True)
        self._dump_thread.start()

    def _dump_worker(self):
        """
        Background worker thread that processes the dump queue.
        Runs forever (daemon thread - dies when the main process exits).
        Pulls (transaction, json_file_path) tuples off the queue and writes them to disk.
        """
        while True:
            try:
                transaction, json_file_path = self._dump_queue.get()
                self.dump_transaction(transaction, json_file_path)
                self._dump_queue.task_done()
            except Exception as e:
                print(f"[DumpWorker] Error writing transaction to storage: {e}")

    def _enqueue_dump(self, transaction, json_file_path):
        """
        Enqueue a transaction to be dumped to storage by the background thread.
        This is non-blocking - the caller returns immediately.
        """
        self._dump_queue.put((transaction, json_file_path))

    def wait_for_pending_dumps(self):
        """
        Block until all queued dump operations have been written to disk.
        Useful for graceful shutdown or when you need to ensure all data is flushed.
        """
        self._dump_queue.join()

    def dump_transaction(self, transaction, json_file_path):
        """
        Writes transaction metadata to a JSON file and received fifragments
        to an associated pickle file. Called by the background dump worker.

        :param transaction: The transaction object to serialize.
        :param json_file_path: Path for the output JSON file.
        """
        transaction_dict = {
            "tid": transaction.tid,
            "file_path": transaction.file_path,
            "state": transaction.state,
            "number_of_packets": transaction.number_of_packets,
            "len_missing_fragments": len(transaction.missing_fragments),
            "missing_fragments": transaction.missing_fragments,
            "start_date": transaction.start_date,
        }
        
        with open(json_file_path, "w") as f:
            json.dump(transaction_dict, f, indent=4)
    
        if len(transaction.fragment_dict) == 0:
            return
    
        pickle_file_path = json_file_path.replace(".json", ".pkl")
        with open(pickle_file_path, "wb") as f:
            pickle.dump(transaction.fragment_dict, f)
    
    def process_create_trans(self, cmd):
        """
        When the command interface receives a command to create a transaction, before sending the command, this will be called
        it should receive the command object and should be the CREATE_TRANS command
        it will create internally the transaction
        """
        
        if not isinstance(cmd, Command):
            print(f"Invalid command type for creating transaction: {type(cmd)}")
            return
        
        if cmd.name != "CREATE_TRANS":
            print(f"Invalid command name for creating transaction: {cmd.name}")
            return
        
        tid = cmd.arguments.get("tid")
        file_path = cmd.arguments.get("string_command")
        
        if tid is None or file_path is None:
            print("Invalid command arguments for creating transaction")
            print(f"Received cmd_arguments: {cmd.arguments}")
            return False

        transaction = self.transaction_manager.create_transaction(tid=tid, file_path=file_path, is_tx=False)
        if transaction is None:
            print(f"Failed to create transaction for command: {cmd}")
            return False
        
        json_file_path = os.path.join(self.session_folder, f"{tid}_{transaction.start_date}.json")
        self._enqueue_dump(transaction, json_file_path)
        
        print(f"Created transaction for command: {cmd} with tid {tid} and file path {file_path}")
        return True
    
    def process_init_trans(self, cmd):
        """
        After gs sending CREATE_TRANS command, the satellite will respond with a INIT command containing more information
        about the transaction. This function will deal with that.
        The extra information provided is the hash and the number of packets.
        """
        
        if not isinstance(cmd, Command):
            print(f"Invalid command type for initializing transaction: {type(cmd)}")
            return False
        
        if cmd.name != "INIT_TRANS":
            print(f"Invalid command name for initializing transaction: {cmd.name}")
            return False
        
        tid = cmd.get_argument("tid")
        number_of_packets = cmd.get_argument("number_of_packets")
        
        transaction = self.transaction_manager.get_transaction(tid=tid, is_tx=False)
        if transaction is None:
            print(f"Failed to find transaction with tid {tid} for initializing transaction")
            return False
        
        transaction.set_number_packets(number_of_packets)
        transaction.change_state(2)

        json_file_path = os.path.join(self.session_folder, f"{tid}_{transaction.start_date}.json")
        self._enqueue_dump(transaction, json_file_path)
        return True
    
    def process_fragment(self, frag):
        """
        Once the transaction has been initialized the gs can request packets from the satellite.
        The satellite will respond with fragment packets containing the data.
        This function processes the received fragment and adds it to the transaction.
        """
        if not isinstance(frag, Fragment):
            print(f"Invalid fragment type for processing fragment: {type(frag)}")
            return False
        
        tid = frag.tid
        
        transaction = self.transaction_manager.get_transaction(tid=tid, is_tx=False)
        if transaction is None:
            print(f"Failed to find transaction with tid {tid} for processing fragment")
            return False
        
        is_completed = transaction.add_fragment(frag)

        json_file_path = os.path.join(self.session_folder, f"{tid}_{transaction.start_date}.json")
        self._enqueue_dump(transaction, json_file_path)
        
        if is_completed:
            print(f"\033[32mTransaction with tid {tid} is completed, all fragments received\033[0m")
            transaction.write_file("downlinked_data")

            # if there is img in file name and type is bin, will try and convert to png
            if "img" in transaction.file_path and transaction.file_path.endswith(".bin"):
                try:
                    input_file = os.path.join("downlinked_data", transaction.file_path)
                    output_file = os.path.join("downlinked_data", f"{transaction.file_path.split('.')[0]}.png")
                    bin_to_png(input_file, output_file)
                except Exception as e:
                    print(f"Failed to convert binary file to PNG: {e}")
        return True        