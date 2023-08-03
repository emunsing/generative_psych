from typing import Any
from pytest import skip
from .test_utils import simple_reflection_api, CONVERSATION_SNIPPETS
from generative_psych import ConversationAgent
from psych_helpers import OpenAIQueryAPI
import logging
logging.basicConfig(level=logging.DEBUG)

LOGGER = logging.getLogger(__name__)

def get_conversation_agent(query_api, name="Alice"):
    return ConversationAgent(query_api=query_api,
                             name=name,
                             background="Alice is a nervous recent college graduate",
                             relationship_goals="Find a partner",
                             other_major_goals="Expressing themselves creatively, finding friendships, developing roots",
                             personal_context="just got off work and looking forward to the evening"
                             )

def test_conversation_agent_init():
    person1 = get_conversation_agent(query_api=None)
    return None

#### Test Snippets

def test_snippet_reflection(caplog):
    caplog.set_level(logging.DEBUG)
    response = """Emotions: Hungry, thirsty\nNeeds: closeness, connection"""
    person1 = get_conversation_agent(query_api=simple_reflection_api(response))
    res = person1.reflect_on_snippets(CONVERSATION_SNIPPETS[2:10])
    assert res == ("hungry", "thirsty", "closeness", "connection")

def test_snippet_reflection_openai():
    query_api = OpenAIQueryAPI(temperature=0.0)
    person1 = get_conversation_agent(query_api=query_api)
    res = person1.reflect_on_snippets(CONVERSATION_SNIPPETS[:10])
    LOGGER.info("Reflection results: \s"+str(res))


### Test Conversations

def test_angry_conversation_reflection():
    response = """Feelings: Angry and resentful that their partner cheated.\nWANTS TO END RELATIONSHIP"""    
    person1 = get_conversation_agent(query_api=simple_reflection_api(response))
    res = person1.reflect_on_conversation(CONVERSATION_SNIPPETS)
    assert res == ("angry and resentful that their partner cheated", True)

def test_positive_conversation_reflection():
    response =  """Feelings: optimistic and excited about the future"""
    person1 = get_conversation_agent(query_api=simple_reflection_api(response))
    res = person1.reflect_on_conversation(CONVERSATION_SNIPPETS)
    assert res == ("optimistic and excited about the future", False)

### Test Chapter 


    

