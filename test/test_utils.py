from typing import Any
from ..generative_psych import ConversationAgent
import logging
logging.basicConfig(level=logging.DEBUG)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel("DEBUG")

CONVERSATION = """
Alice: Hey Bob, how's it going?

Bob: Hi Alice! I'm doing great, thanks for asking. How about you?

Alice: I'm good too, thanks. Just had a productive day at work. Anything interesting happening with you?

Bob: Actually, yes! I just got back from a weekend trip to the beach. The weather was fantastic, and I had a great time.

Alice: That sounds amazing! I could use a beach getaway myself. Did you do any water activities?

Bob: Oh, definitely! I went snorkeling and even tried my hand at paddleboarding. It was so much fun exploring the underwater world and testing my balance on the board.

Alice: Wow, I'm a bit jealous now. It must have been quite an adventure. Did you see any interesting marine life while snorkeling?

Bob: Absolutely! I spotted colorful fish, coral reefs, and even a sea turtle. It was mesmerizing to observe them in their natural habitat. I managed to capture some incredible photos too.

Alice: That's fantastic, Bob! I'd love to see those photos sometime. It sounds like you had a truly unforgettable experience. By the way, did you try any local cuisine?

Bob: Oh, yes! I indulged in some delicious seafood dishes. Freshly grilled fish, shrimp, and calamari were some of the highlights. The coastal restaurants had an amazing variety to choose from.

Alice: Yum, seafood is my weakness! I can almost taste it just thinking about it. It seems like you had the perfect combination of adventure and relaxation on your trip. Any memorable moments that stood out?

Bob: Definitely! One evening, I watched the sunset from the beach, and it was breathtaking. The sky turned into a canvas of vibrant colors, and it felt like time stood still. It was a serene moment that I'll cherish.

Alice: Oh, that sounds absolutely magical. Sunsets have a way of creating such a peaceful atmosphere. I'm glad you got to experience that. So, what's next on your agenda now that you're back?

Bob: Well, I need to catch up on some work and sort out a few pending tasks. But I'm already planning my next adventure. Maybe a hiking trip to the mountains this time.

Alice: That sounds like a great plan! Nature has so much to offer, whether it's the beach or the mountains. I hope your upcoming adventure is just as exciting. Let me know how it goes!

Bob: Absolutely, Alice! I'll be sure to keep you updated. And if you ever decide to go on a beach getaway or need any travel recommendations, feel free to ask. I'm here to help!

Alice: Thanks, Bob! I appreciate that. I'll definitely keep that in mind. Enjoy getting back into the swing of things, and I'll catch up with you soon.

Bob: Sounds good, Alice! Take care and talk to you soon. Have a wonderful day!"""

CONVERSATION_SNIPPETS = [l for l in CONVERSATION.split("\n") if l != '']

class simple_reflection_api:
    def __init__(self, response):
        self.response = response
    def __call__(self, *args: Any, **kwds: Any) -> Any:
            query = args[0].replace("    ", "")
            LOGGER.info(f"Query: {args[0]}")
            LOGGER.info(f"Response: {self.response}")
            return self.response
