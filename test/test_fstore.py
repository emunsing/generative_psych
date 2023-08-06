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

def test_create_append_conversation():
    test_uid1 = 'testuid'
    test_uid2 = 'anothertestuid'

    with tempfile.TemporaryDirectory() as tempdir:
        store = FileNarrativeStore(data_dir=tempdir)
        store.create_conversation_record(test_uid1)
        store.append_conversation_record(['hello, Alice!', 'hello, Bob!'])

        expected_fpath = os.path.join(tempdir, 
                                      store.narrative_dir_format.format(idx=1, uid=test_uid1), 
                                      store.conversation_file_format.format(idx=0))
        with open(expected_fpath, 'r') as f:
            assert f.read() == 'hello, Alice!\nhello, Bob!\n'

        store.append_conversation_record(['heya, Charlie!', 'howdy, Dahlia!'])
        with open(expected_fpath, 'r') as f:
            assert f.read() == 'hello, Alice!\nhello, Bob!\nheya, Charlie!\nhowdy, Dahlia!'

        store.create_conversation_record(test_uid)