from datastore import FileNarrativeStore
import tempfile
import os
import json

def test_init():
    with tempfile.TemporaryDirectory() as tempdir:
        store = FileNarrativeStore(data_dir=tempdir)
        with open(store.narrative_index_fpath, 'r') as f:
            assert json.load(f) == {}
        with open(store.reader_position_fpath, 'r') as f:
            assert json.load(f) == [0, 0]
        with open(store.uid_index_fpath, 'r') as f:
            assert json.load(f) == {}

def test_filenarrative_workflow():
    test_uid1 = 'testuid'
    test_uid2 = 'anothertestuid'

    with tempfile.TemporaryDirectory() as tempdir:
        store = FileNarrativeStore(data_dir=tempdir)
        store.create_conversation_record(test_uid1)
        store.append_conversation_record(['hello, Alice!', 'hello, Bob!'])

        expected_fpath = os.path.join(tempdir, 
                                      store.narrative_dir_format.format(idx=0), 
                                      store.conversation_file_format.format(idx=0))
        with open(expected_fpath, 'r') as f:
            assert f.read() == 'hello, Alice!\nhello, Bob!\n'

        store.append_conversation_record(['heya, Charlie!', 'howdy, Dahlia!'])
        with open(expected_fpath, 'r') as f:
            assert f.read() == 'hello, Alice!\nhello, Bob!\nheya, Charlie!\nhowdy, Dahlia!\n'

        store.create_conversation_record(test_uid1)
        store.append_conversation_record(['hello again, Alice!', 'hello again, Bob!', 'I am ghosting you!', 'END OF NARRATIVE'])
        expected_fpath = os.path.join(tempdir, 
                                      store.narrative_dir_format.format(idx=0), 
                                      store.conversation_file_format.format(idx=1))
        expected_output = 'hello again, Alice!\nhello again, Bob!\nI am ghosting you!\nEND OF NARRATIVE\n'
        with open(expected_fpath, 'r') as f:
            assert f.read() == 'hello again, Alice!\nhello again, Bob!\nI am ghosting you!\nEND OF NARRATIVE\n'
        file_getter_output = store.get_conversation_record(store.get_set_narrative_idx(test_uid1), 1)
        assert file_getter_output == expected_output
        
        store.create_conversation_record(test_uid2)
        store.append_conversation_record(['hello, Anna!', 'hello, Billy!'])
        expected_fpath = os.path.join(tempdir, 
                                      store.narrative_dir_format.format(idx=1), 
                                      store.conversation_file_format.format(idx=0))
        with open(expected_fpath, 'r') as f:
            assert f.read() == 'hello, Anna!\nhello, Billy!\n'

        assert store.count_unread_conversations() == 2

        assert store.get_next_conversation_index(0, 0) == (0, 1)
        assert store.get_next_conversation_index(0, 1) == (1, 0)
