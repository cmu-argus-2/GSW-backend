"""
This file will implement the class that will be used by the ground station to deal with the transactions

when the ground station gets a command to create a transaction this class will be called before to create the transaction
when a transaction packet is received this class will also be called and deal with the packet

It will eventually also deal with storing the transaction in storage
    the main idea behind this is to minimize the chances of losing a transaction. it will allow you to recover lost transactions

"""
import pickle
import json
from lib.telemetry.splat.splat.transport_layer import TransactionManager, Fragment, Command
import os
import time


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
        
    def dump_transaction(self, transaction, json_file_path):
        """
        Docstring for dump_transaction
        
        :param self: Description
        :param transaction: Description
        :param json_file_path: Description
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
        
        # dump the json file
        with open(json_file_path, "w") as f:
            json.dump(transaction_dict, f, indent=4)
    
        # check if we have received any packets yet
        if len(transaction.fragment_dict) == 0:
            return
    
        # dump the pickle file
        # we will just change the extension to .pkl and dump the missing packets dict
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

        # create the transaction
        transaction = self.transaction_manager.create_transaction(tid=tid, file_path=file_path, is_tx=False)
        if transaction is None:
            print(f"Failed to create transaction for command: {cmd}")
            return False
        
        # create the json with the transaction information
        json_file_name = f"{tid}_{transaction.start_date}.json"
        json_file_path = os.path.join(self.session_folder, json_file_name)
        self.dump_transaction(transaction, json_file_path)
        
        print(f"Created transaction for command: {cmd} with tid {tid} and file path {file_path}")
        # was able to create the transaction 
        return True
    
    def process_init_trans(self, cmd):
        """
        After gs sending CREATE_TRANS command, the satellite will respond with a INIT command containing more information
        about the transaction. This function will deal with that
        the extra information provided is the hash and the number of packets
        but for now we are ignoring the hash
        
        the command passed here should be the INIT_TRANS command
        """
        
        if not isinstance(cmd, Command):
            print(f"Invalid command type for initializing transaction: {type(cmd)}")
            return False
        
        if cmd.name != "INIT_TRANS":
            print(f"Invalid command name for initializing transaction: {cmd.name}")
            return False
        
        tid = cmd.get_argument("tid")
        number_of_packets = cmd.get_argument("number_of_packets")
        
        # find the transaction with the tid
        transaction = self.transaction_manager.get_transaction(tid=tid, is_tx=False)
        if transaction is None:
            print(f"Failed to find transaction with tid {tid} for initializing transaction")
            return False
        
        # update the transaction with the number of packets
        transaction.set_number_packets(number_of_packets)
        
        # change the state of the transaction
        transaction.change_state(2)   # [check] - do we need the states? if so remove the hardcode here
        self.dump_transaction(transaction, os.path.join(self.session_folder, f"{tid}_{transaction.start_date}.json"))
        return True
    
    def process_fragment(self, frag):
        """
        Once the transaction has been initialized the gs can request packets from the satellite
        the satellite will respond with fragments packets containing the data
        this function will process the received fragment and add it to the transaction
        """
        if not isinstance(frag, Fragment):
            print(f"Invalid fragment type for processing fragment: {type(frag)}")
            return False
        
        tid = frag.tid   # need to tid to find the transaction
        
        # find the transaction with the tid
        transaction = self.transaction_manager.get_transaction(tid=tid, is_tx=False)
        if transaction is None:
            print(f"Failed to find transaction with tid {tid} for processing fragment")
            return False
        
        # add the fragment to the transaction
        is_completed = transaction.add_fragment(frag)
        
        # save the transaction information in the json and pickle file
        self.dump_transaction(transaction, os.path.join(self.session_folder, f"{tid}_{transaction.start_date}.json"))
        
        if is_completed:
            #print in green
            
            print(f"\033[32mTransaction with tid {tid} is completed, all fragments received\033[0m")
            transaction.write_file("downlinked_data")        
        return True
        