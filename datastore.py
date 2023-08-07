import glob
import os
import json
import hashlib
import abc


class NarrativeStore(abc.ABC):
    """
    Writer affordances: 
    - Create narrative record
    - Get most recent conversation
    - Create conversation record
    - Append to conversation record
    - Check where the reader is (narrative index, conversation index)
    - Compute how many conversations are between the reader and the writer
    
    Reader affordances:
    - Get conversation record
    - Get next conversation record
    - Save current position

    Data model:
    - Store conversations in records
    - Allow for indexing by narrative id and by conversation id
    - Allow for easy counting of the number of conversations in each narrative
    - Store the current (narrative id, convesation_id) for reader
    """
    
    @abc.abstractmethod
    def create_conversation_record(self, narrative_uid):
        # Should also update the conversation structure model if needed
        pass

    @abc.abstractmethod
    def append_conversation_record(self):
        pass

    @abc.abstractmethod
    def get_conversation_record(self, narrative_index, conversation_index):
        pass

    @abc.abstractmethod
    def get_next_conversation_index(self, current_narrative_index, current_conversation_index):
        pass
    
    @abc.abstractmethod
    def save_reader_position(self, narrative_index, conversation_index):
        pass

    @abc.abstractmethod
    def count_unread_conversations(self):
        pass


class FileNarrativeStore(NarrativeStore):
    """
    - Each narrative stored in a different folder, numbered sequentially
    - Each conversation stored in a different file, numbered sequentially
    - Dict Mapping of Narrative UIDs to folder indices in self.uid_index_fpath
    - Numeric tree structure as dict in self.narrative_index_fpath
    """
    def __init__(self, data_dir=None):
        self.data_dir = data_dir
        self.narrative_dir_format = '{idx}'
        self.conversation_file_format = '{idx}.txt'
        self.narrative_index_fpath = os.path.join(self.data_dir, 'narrative_index.json')
        self.reader_position_fpath = os.path.join(self.data_dir, 'reader_position.json')
        self.uid_index_fpath = os.path.join(self.data_dir, 'uid_index.json')

        self.initialize_datadir()

    def initialize_datadir(self):
        if not os.path.exists(self.data_dir):
            os.makedir(self.data_dir)
        if len(os.listdir(self.data_dir)) == 0:
            with open(self.narrative_index_fpath, 'w') as f:
                json.dump({}, f)
            with open(self.reader_position_fpath, 'w') as f:
                json.dump((0, 0), f)
            with open(self.uid_index_fpath, 'w') as f:
                json.dump({}, f)

    def get_uid_index(self):
        with open(self.uid_index_fpath, 'r') as f:
            return json.load(f)
    
    def get_narrative_tree(self):
        with open(self.narrative_index_fpath, 'r') as f:
            return json.load(f)
        
    def get_head_narrative_idx(self):
        uid_index = self.get_uid_index()
        return max(uid_index.values())

    def get_set_narrative_idx(self, narrative_uid:str=None):
        if narrative_uid is None:
            return self.get_head_narrative_idx()
        uid_index = self.get_uid_index()
        idx = uid_index.get(narrative_uid, len(uid_index))
        uid_index[narrative_uid] = idx
        with open(self.uid_index_fpath, 'w') as f:
            json.dump(uid_index, f)

        full_dir_path = os.path.join(self.data_dir, self.narrative_dir_format.format(idx=idx))
        if not os.path.exists(full_dir_path):
            os.mkdir(full_dir_path)        
        return idx
    
    def format_fpath(self, narrative_idx, conversation_idx):
        return os.path.join(self.data_dir, 
                            self.narrative_dir_format.format(idx=narrative_idx),
                            self.conversation_file_format.format(idx=conversation_idx))

    def get_conversation_fpath(self, narrative_uid:str=None, conversation_index:int=None):
        # If narrative_uid is None, look in the most recent narrative
        # If conversation_index is None, return the most recent conversation
        narrative_idx = self.get_set_narrative_idx(narrative_uid)

        if conversation_index is None:
            # Get the head index from the 
            narrative_tree = self.get_narrative_tree()
            conversation_index = narrative_tree[str(narrative_idx)][-1]
        return self.format_fpath(narrative_idx, conversation_index)

    def create_conversation_record(self, narrative_uid):
        narrative_idx = self.get_set_narrative_idx(narrative_uid) # Force creation of a new directory
        narrative_tree = self.get_narrative_tree()
        current_conversation_list = narrative_tree.get(str(narrative_idx), [])
        new_conversation_index = len(current_conversation_list)
        narrative_tree[str(narrative_idx)] = current_conversation_list + [new_conversation_index]
        with open(self.narrative_index_fpath, 'w') as f:
            json.dump(narrative_tree, f)
        with open(self.format_fpath(narrative_idx, new_conversation_index), 'w') as f:
            pass
        return 

    def append_conversation_record(self, lines:list):
        # Get the most recent conversation
        with open(self.get_conversation_fpath(), 'a') as f:
            for line in lines:
                f.write(f'{line}\n')
        
    def get_conversation_record(self, narrative_index, conversation_index):
        conversation_fpath = self.format_fpath(narrative_index, conversation_index)
        with open(conversation_fpath, 'r') as f:
            return f.read()

    def count_unread_conversations(self):
        narrative_tree = self.get_narrative_tree()
        with open(self.reader_position_fpath, 'r') as f:
            reader_pos = json.load(f)
        remaining_chapters = narrative_tree[str(reader_pos[0])][-1] - reader_pos[1]
        for narrative_idx in range(reader_pos[0]+1, len(narrative_tree)):
            remaining_chapters += len(narrative_tree[str(narrative_idx)])
        return remaining_chapters

    def get_next_conversation_index(self, current_narrative_index, current_conversation_index):
        narrative_tree = self.get_narrative_tree()
        if current_conversation_index + 1 < len(narrative_tree[str(current_narrative_index)]):
            return current_narrative_index, current_conversation_index + 1
        else:
            return current_narrative_index + 1, 0

    def save_reader_position(self, narrative_index, conversation_index):
        with open(self.reader_position_fpath, 'w') as f:
            json.dump((narrative_index, conversation_index), f)
