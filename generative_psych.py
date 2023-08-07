import logging
import numpy as np
import re
from collections import OrderedDict
import textwrap
import json
import hashlib
import abc

import logging

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel("INFO")

class ConversationAgent:

    def __init__(self, query_api, name, background, relationship_goals, other_major_goals, personal_context) -> None:
        self.query_api = query_api
        self.name = name
        self.background = background  # Complete sentences
        self.relationship_goals = relationship_goals
        self.other_major_goals = other_major_goals
        self.conversation_context = ''
        self.personal_context = personal_context
        self.main_emotion = "relaxed"
        self.secondary_emotion = "curious"
        self.primary_need = "closeness"
        self.secondary_need = "self-actualization"
        self.view_of_other = "curious and attracted"
        self.wants_relationship_to_end = False
        self.uid = self.make_uid()

    def make_uid(self):
        # Current representation of object- will change over time, whether that's desired or not
        attrs = vars(self)
        string_vars = {k: v for k, v in attrs.items() if isinstance(v, str)}
        string_repr = json.dumps(string_vars, sort_keys=True)
        return hashlib.sha256(string_repr.encode()).hexdigest()

    def update_personal_context(self):
        context_options = [
                            # (context, main_emotion, secondary_emotion, primary_need, secondary_need)
                           ('had a good day at work where they accomplished something meaningful', 'proud', 'upbeat', 'being seen', 'connection'),
                           ('had a bad day at work where they received negative feedback', 'frustrated', 'glum', 'independence', 'appreciation'),
                           ('came down with a cold', 'sick', 'tired', 'rest', 'care'),
                           ('read some disheartening news', 'discouraged', 'fearful', 'connection', 'reassurance'),
                           ('Woke up feeling worried about the state of the world', 'anxious', 'depressed', 'self-acceptance', 'inspiration'),
                           ('Woke up feeling optimistic about the state of the world', 'enthusiastic', 'curious', 'adventure', 'play'),
                           ('had a great workout', 'radiant', 'upbeat', 'stimulation', 'spontaneity'),
                           ('had a really great day', 'enlivened', 'refreshed', 'relaxation', 'humor'),
                           ('had a bad interaction with a friend', 'dejected', 'angry', 'mutuality', 'affection'),
                           ]
        
        choice_index = np.random.choice(len(context_options))
        self.personal_context, self.main_emotion, self.secondary_emotion, self.primary_need, self.secondary_need = context_options[choice_index]


    def get_current_status(self):
        prompt = textwrap.dedent(f"""\
                    {self.background}.
                    {self.name} currently hopes that the relationship will help them {self.relationship_goals.lower()} and has been feeling {self.view_of_other.lower()} toward their partner.
                    {self.name} is also balancing the relationship with other major goals of {self.other_major_goals.lower()}.
                    Before this conversation, {self.name} {self.personal_context.lower()}.
                    {self.name} is currently feeling {self.main_emotion} and {self.secondary_emotion}, and needs {self.primary_need}. {self.name} also is beginning to feel a need for {self.secondary_need}.
                    """)
        if self.wants_relationship_to_end:
            prompt += f"""{self.name} is also considering ending the relationship."""
        
        return prompt

    def reflect_on_snippets(self, snippets):
        # Based on a set of snippets, update the emotions and needs
        formatted_snippets = "\n".join(snippets)
        prompt =  self.get_current_status() + textwrap.dedent(f"""\
                    
                    
                    Based on the following section of conversation, what is {self.name} feeling and needing?
                    First, output "Emotions:" followed by two main emotions, separated by commas.
                    Then on a new line output "Needs:" followed by two main emotional needs, separated by commas.

                    Conversation:
                    """) + formatted_snippets
        
        res = self.query_api(prompt)

        query_conditions = [len(res.split("\n")) == 2, 'Emotions:' in res, 'Needs:' in res, 
                            len(res.split('\n')[0].split("Emotions:")[1].split(",")) == 2, 
                            len(res.split('\n')[1].split("Needs:")[1].split(",")) == 2]
        
        if not all(query_conditions):
            logging.warning("Poorly formatted reflect_on_snippets response. Returning current values")
        else:
            self.main_emotion, self.secondary_emotion = [s.strip() for s in res.split('\n')[0].split("Emotions: ")[1].lower().split(",")]
            self.primary_need, self.secondary_need = [s.strip() for s in res.split('\n')[1].split("Needs: ")[1].lower().split(",")]
        return self.main_emotion, self.secondary_emotion, self.primary_need, self.secondary_need

    def reflect_on_conversation(self, conversation_block):
        # Based on a set of snippets, update the person's feelings toward their partner
        formatted_conversation = "\n".join(conversation_block)
        prompt =  self.get_current_status() + textwrap.dedent(f"""\
                
                
                The following is a conversation between {self.name} and their partner. The two of them {self.conversation_context}. Summarize how this conversation would change how {self.name} feels about their partner.
                First, print "Feelings:" with a few words, e.g. 'curious and attracted to their new date' or 'angry and resentful for being lied to'. The summary of feelings should be at most one sentence.
                If {self.name} would want to end the relationship, on a new line print "WANTS TO END RELATIONSHIP".

                Conversation:
                """) + formatted_conversation
        res = self.query_api(prompt)

        query_conditions = [len(res.split("\n")) <= 2, 'Feelings:' in res]

        if not all(query_conditions):
            logging.warn("Poorly formatted reflect_on_conversation response. Returning current values")
        else:
            self.view_of_other = res.split('\n')[0].split("Feelings:")[1].lower().replace('.', '').strip()
            self.wants_relationship_to_end = "WANTS TO END RELATIONSHIP" in res

        return self.view_of_other, self.wants_relationship_to_end

    def reflect_on_chapter(self, chapter_block):
        # Based on a longer set of conversations between a person and their partner, update the person's view of their own goals and their goals for the relationship.
        
        prompt = self.get_current_status() + textwrap.dedent(f"""\

                    Below is a summary of events which unfolded between {self.name} and their partner.
                    How would these events change {self.name}'s goals for the relationship? Output a line beginning with "Relationship goals:" and a succinct summary (e.g. "get married" or "break up")
                    Would these events change {self.name}'s other life goals? Output a line beginning with "Other goals:" and a succinct summary of their other goals, which may not change.

                    """) + chapter_block
        res = self.query_api(prompt)

        query_conditions = [len(res.split("\n")) <= 2, 'Relationship goals:' in res, "Other goals:" in res]

        if not all(query_conditions):
            logging.warn("Poorly formatted reflect_on_conversation response. Returning current values")
        else:
            self.relationship_goals = res.split('\n')[0].split("Relationship goals:")[1].lower().replace('.', '').strip()
            self.other_major_goals = res.split('\n')[0].split("Relationship goals:")[1].lower().replace('.', '').strip()
        
        return self.relationship_goals, self.other_major_goals
        


class RelationshipConversationContext():
    """
    Relationship context manager, forcing new events into the course of a relationship.
    """

    def __init__(self, query_api, narrative_store, person1, person2) -> None:
        self.query_api = query_api
        self.narrative_store = narrative_store
        self.person1 = person1
        self.person2 = person2
        self.snippet_overlap = 4
        self.snippet_truncate = 0
        self.reflection_interval = 3
        self.rounds_in_conversation = 0
        self.max_rounds_in_conversation = np.inf
        self.conversations_in_chapter = 0
        self.total_conversations = 0
        self.continue_conversation = True
        self.continue_relationship = True
        self.narrative_uid = hashlib.sha256((self.person1.uid + self.person2.uid).encode()).hexdigest()

        # Context should be a passive description of stage of relationship, which can be used like "two people who ___"
        self.conversation_context = "are on their first date"
        self.person1.conversation_context = self.conversation_context
        self.person2.conversation_context = self.conversation_context
        

    @property
    def chapter_progression_rate(self):
        return OrderedDict([("are on their first date", 1.0),  # Progression = probability of changing state
                            ("recently started dating", 0.4),
                            ("have been dating regularly for a few months", 0.05),
                            ("recently moved in together", 0.2),
                            ("have moved in together and feel stable", 0.6),
                            ("ending the relationship", 0.0),
                            ])

    def update_conversation_context(self):
        # This model of conversation progression progresses numerically through a set of chapter descriptions, based on a survival rate.
        
        current_survival_rate = self.chapter_progression_rate[self.conversation_context]
        if np.random.rand() < current_survival_rate:
            current_chapter_number = list(self.chapter_progression_rate.keys()).index(self.conversation_context)
            self.conversation_context = list(self.chapter_progression_rate.keys())[current_chapter_number + 1]
            self.person1.conversation_context = self.conversation_context
            self.person2.conversation_context = self.conversation_context
            self.conversations_in_chapter = 0

    def get_general_prompt(self):
        assignment = textwrap.dedent(f"""\
                        You are writing a dialogue between {self.person1.name} and {self.person2.name}, two people in a relationship who {self.conversation_context}.
                        The conversation should be realistic, accurate, and ongoing. Each line of the dialogue should start on a new line,
                        with the speaker indicated by "{self.person1.name}:" or "{self.person2.name}:".
                        If the dialogue has come to its natural end and both people want it to end, print "END CONVERSATION" on a new line.
                        If both people need to end the relationship, print "END NARRATIVE" on a new line.
                        """).replace("\n", " ")

        general_prompt = assignment + textwrap.dedent("""\
                        
                        
                        Here is some background on {p1name}:
                        {p1status}

                        Here is some background on {p2name}:
                        {p2status}
                        """).format(p1name=self.person1.name, p1status=self.person1.get_current_status(), 
                                    p2name=self.person2.name, p2status=self.person2.get_current_status())
        
        return general_prompt
    
    def start_conversation(self):
        self.continue_conversation = True
        res = self.query_api(self.get_general_prompt())
        return re.split('\n\n|\n', res)

    def advance_conversation(self, snippets):
        final_prompt = self.get_general_prompt() + "\nHere is the most recent portion of the conversation:\n\n" + "\n".join(snippets)
        res = self.query_api(final_prompt)
        return re.split('\n\n|\n', res)
    
    def run_conversation(self):
        # Get snippets
        # Check if the conversation ended
        # if ended: 
        # if not: 
#           truncate snippets
        # Remove break snippets from converation
        # truncate snippets
        # 
        self.narrative_store.create_conversation_record(self.narrative_uid)
        self.continue_conversation = True
        snippets_since_last_reflection = []
        conversation_snippets = self.start_conversation()
        snippets_since_last_reflection += conversation_snippets
        self.rounds_in_conversation = 1
        self.check_conversation_ended(conversation_snippets)       

        while self.continue_conversation:
            if self.snippet_truncate:
                # Used for language models which tend to wrap up conversations early
                conversation_snippets = conversation_snippets[:-self.snippet_truncate]
                snippets_since_last_reflection = snippets_since_last_reflection[:-self.snippet_truncate]

            if self.rounds_in_conversation % self.reflection_interval == 0:
                LOGGER.info(f"{self.person1.name} is reflecting on the conversation")
                self.person1.reflect_on_snippets(conversation_snippets)
                LOGGER.info(f"{self.person2.name} is reflecting on the conversation")
                self.person2.reflect_on_snippets(conversation_snippets)
                snippets_since_last_reflection = []
            
            conversation_snapshot = conversation_snippets[-min(self.snippet_overlap, len(conversation_snippets)):]
            new_snippets = self.advance_conversation(conversation_snapshot)
            snippets_since_last_reflection += new_snippets
            conversation_snippets += new_snippets
            self.rounds_in_conversation += 1
            self.check_conversation_ended(conversation_snippets)

        self.narrative_store.append_conversation_record(conversation_snippets)
        self.check_narrative_ended(conversation_snippets)
        if self.continue_relationship:
            self.person1.reflect_on_conversation(conversation_snippets)
            self.person2.reflect_on_conversation(conversation_snippets)
            # # TODO
            # self.person1.summarize_conversation(conversation_snippets)
            # self.person2.summarize_conversation(conversation_snippets)
            # self.person1.reflect_on_chapter(conversation_snippets)
            # self.person2.reflect_on_chapter(conversation_snippets)

    def check_conversation_ended(self, snippets):
        if "END CONVERSATION" in snippets or "END NARRATIVE" in snippets or self.rounds_in_conversation >= self.max_rounds_in_conversation:
            self.total_conversations += 1
            self.continue_conversation = False

    def check_narrative_ended(self, snippets):
        if "END NARRATIVE" in snippets:
            self.continue_relationship = False

    def run_relationship(self):
        while self.continue_relationship:
            self.run_conversation()
            self.conversations_in_chapter += 1
            self.update_conversation_context()
            self.person1.update_personal_context()
            self.person2.update_personal_context()
        print("END OF NARRATIVE")
