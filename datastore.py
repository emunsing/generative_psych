import glob
import os
import json
import hashlib
import abc


class NarrativeStore(abc.ABCMeta):
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
    def create_conversation_record():
        # Should also update the conversation structure model if needed
        pass

    @abc.abstractmethod
    def append_conversation_record():
        pass

    @abc.abstractmethod
    def get_conversation_record(narrative_index, conversation_index):
        pass

    @abc.abstractmethod
    def get_next_conversation_index(current_narrative_index, current_conversation_index):
        pass
    
    @abc.abstractmethod
    def save_reader_position(narrative_index, conversation_index):
        pass

    @abc.abstractmethod
    def compute_conversation_distance(nidx1, cidx1, nidx2, cidx2):
        pass


class FileNarrativeStore():
    """
    
    """
    def __init__(self, data_dir=None):
        self.data_dir = data_dir
        self.narrative_dir_format = '{idx}_{uid}'
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


    def head_narrative_handler(self, narrative_uid:[str, None]=None):
        narrative_dirs = os.walk(self.data_dir).__next__()[1]
        if len(narrative_dirs) > 0:
            dir_tups = [d.split("_") for d in narrative_dirs]
            dir_tups = sorted(dir_tups, key=lambda t: t[0])
            dirs_matching_uid = [t for t in dir_tups if t[1] == narrative_uid]
            most_recent_index, most_recent_hash = dir_tups[-1]
            if narrative_uid is None:
                # Main exit point for simple query, returning the most recent directory
                return self.narrative_dir_format.format(idx=most_recent_index, uid=most_recent_hash)
            else:
                assert len(dirs_matching_uid) == 0 or most_recent_hash == narrative_uid, "UID exists in a directory that is not the most recent"
        else:
            assert narrative_uid is not None, "No current directories and no narrative UID provided"
            most_recent_index, most_recent_hash = 0, ''

        if most_recent_hash == narrative_uid:
            return self.narrative_dir_format.format(idx=most_recent_index, uid=most_recent_hash)
        else:
            novel_idx = most_recent_index+1
            with open(self.uid_index_fpath, 'r') as f:
                uid_index_map = json.load(f)
            uid_index_map[narrative_uid] = novel_idx
            with open(self.uid_index_fpath, 'w') as f:
                json.dump(uid_index_map, f)

            dirname = self.narrative_dir_format.format(idx=novel_idx, uid=narrative_uid)
            os.makedirs(os.path.join(self.data_dir, dirname))
            return dirname  

    def make_head_narrative_dir(self, narrative_uid:str):
        # If the narrative uid is not the most recent narrative, create a new directory
        # Raise an error if the narrative_uid is already in the narrative list, but not the most recent
        # return the narrative directory
        return self.head_narrative_handler(narrative_uid)
        
    def get_head_narrative_dir(self):
        return self.head_narrative_handler()
    
    def get_narrative_dir(self, narrative_uid:str=None):
        # Get a specific narrative directory's path, or the head path if narrative_uid=None
        if narrative_uid is None:
            return self.get_head_narrative_dir()
        narrative_dirs = os.walk(self.data_dir).__next__()[1]
        assert len(narrative_dirs) > 0, "No narrative directories found"
        match_dir = [d for d in narrative_dirs if narrative_uid in d][0]
        return match_dir

    def get_head_conversation_index(self, narrative_uid:str=None):
        narrative_dir = self.get_narrative_dir(narrative_uid)
        conversation_files = os.walk(os.path.join(self.data_dir, narrative_dir)).__next__()[2]
        if len(conversation_files) > 0:
            current_conversation_index = max([int(f.split(".")[0]) for f in conversation_files])
            return current_conversation_index
        else:
            return 0

    def get_conversation_fpath(self, narrative_uid:str=None, conversation_index:int=None):
        # If narrative_uid is None, look in the most recent narrative
        # If conversation_index is None, return the most recent conversation
        narrative_dir = self.get_narrative_dir(narrative_uid)
        if conversation_index is None:
            conversation_index = self.get_head_conversation_index(narrative_uid)
        return os.path.join(self.data_dir, narrative_dir, self.conversation_file_format.format(idx=conversation_index))

    def create_conversation_record(self, narrative_uid):
        narrative_dir = self.make_head_narrative_dir(narrative_uid)
        current_conversation_index = self.get_head_conversation_index(narrative_uid)
        with open(self.get_conversation_fpath(narrative_uid), 'w') as f:
            pass
        with open(self.narrative_index_fpath, 'r') as f:
            narrative_tree = json.load(f)
        narrative_idx = narrative_dir.split("_")[0]
        narrative_tree[narrative_idx] = current_conversation_index + 1
        with open(self.narrative_index_fpath, 'w') as f:
            json.dump(narrative_tree, f)

    def append_conversation_record(self, lines:list):
        with open(self.get_conversation_fpath(), 'a') as f:
            for line in lines:
                f.write(f'{line}\n')
        
    def count_unread_conversations(self):
        with open(self.narrative_index_fpath, 'r') as f:
            narrative_tree = json.load(f)
        with open(self.reader_position_fpath, 'r') as f:
            reader_pos = json.load(f)
        remaining_chapters = narrative_tree[reader_pos[0]] - reader_pos[1]
        for narrative_idx in range(reader_pos[0]+1, len(narrative_tree)):
            remaining_chapters += narrative_tree[narrative_idx]
        return remaining_chapters