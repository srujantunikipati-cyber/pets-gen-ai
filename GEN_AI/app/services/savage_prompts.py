"""Service for generating savage roast prompts for pet videos."""

import random
import logging

_logger = logging.getLogger(__name__)


class SavagePromptGenerator:
    """Generates savage and funny roast prompts for pet videos."""

    # Savage roast prompts for dogs
    DOG_ROASTS = [
        "This dog thinks they're the main character, but they can barely catch a treat thrown right at them",
        "Looking at this pup like they invented loyalty, when they'd sell you out for a single bacon strip",
        "This dog acts all tough but probably barks at their own reflection and loses every time",
        "Seriously? This furball really thinks chasing their tail counts as cardio",
        "This dog walks around like they own the place, but they still can't figure out how doors work",
        "Acting all majestic when everyone knows they eat grass and immediately throw it up",
        "This pooch thinks they're intimidating but they're literally scared of vacuum cleaners",
        "Look at this doggo acting cool when they probably still haven't mastered not peeing when excited",
        "This dog really said 'I'm adorable' then proceeded to eat something questionable from the trash",
        "Walking around with that confident energy but can't even catch a ball without it hitting their face",
        "This pup thinks they're a guard dog but probably hides behind you during thunderstorms",
        "Acting all sophisticated when everyone saw you fail at jumping on the couch three times in a row",
        "This dog really thinks sitting pretty will hide the fact they just destroyed your favorite shoes",
        "Looking majestic here but we all know you run away from butterflies",
        "This furball acts tough but probably cries when you pretend to throw the ball and don't",
    ]

    # Savage roast prompts for cats
    CAT_ROASTS = [
        "This cat thinks they're royalty but they literally eat food off the floor",
        "Looking all mysterious when you literally just knocked a glass off the table for fun",
        "This cat acts independent but screams bloody murder when you're 5 minutes late with dinner",
        "Acting all graceful when everyone saw that failed jump where you slid off the counter",
        "This feline thinks they're untouchable but they run from cucumbers like their life depends on it",
        "Looking elegant here but you literally just tried to bury your poop on a hardwood floor",
        "This cat walks around judging everyone but can't even catch a laser pointer dot",
        "Acting mysterious when you literally just got scared by your own tail",
        "This kitty thinks they're a hunter but probably got outsmarted by a toy mouse today",
        "Looking all cute when you just spent 20 minutes staring at a wall for no reason",
        "This cat acts superior but probably meowed at a door that was already open",
        "Acting all mighty when you literally fit in a box half your size like that's an accomplishment",
        "This feline thinks they're intimidating but you literally purr when someone scratches your chin",
        "Looking fierce here but you probably ran away from a harmless bug five minutes ago",
        "This cat walks around like they own you, and honestly they probably do but still",
    ]

    # General pet roasts that work for any animal
    GENERAL_PET_ROASTS = [
        "This pet really woke up and chose chaos today, and honestly it shows",
        "Looking all innocent when everyone knows the mess you just made in the other room",
        "This little troublemaker thinks cute privilege will save them from everything, and they're right",
        "Acting all sweet when you literally just caused property damage 10 minutes ago",
        "This pet's cuteness is the only thing preventing a lecture right now",
        "Looking adorable here but your owner's patience is being tested daily",
        "This furball thinks being cute excuses everything and unfortunately they're not wrong",
        "Acting all precious when you're literally the reason your human can't have nice things",
        "This pet's expression says 'I did nothing wrong' but the evidence suggests otherwise",
        "Looking innocent here but everyone knows you're planning your next mischief",
    ]

    def __init__(self):
        """Initialize the savage prompt generator."""
        self.all_prompts = (
            self.DOG_ROASTS + 
            self.CAT_ROASTS + 
            self.GENERAL_PET_ROASTS
        )
        _logger.info(f"🔥 Savage Prompt Generator initialized with {len(self.all_prompts)} roasts")

    def generate_savage_prompt(self, pet_type: str = "general") -> str:
        """Generate a random savage roast prompt.
        
        Args:
            pet_type: Type of pet (dog, cat, or general)
            
        Returns:
            A savage roast prompt string
        """
        pet_type = pet_type.lower()
        
        if pet_type == "dog":
            prompt = random.choice(self.DOG_ROASTS)
        elif pet_type == "cat":
            prompt = random.choice(self.CAT_ROASTS)
        else:
            # Use general prompts or mix of all
            prompt = random.choice(self.all_prompts)
        
        _logger.info(f"🔥 Generated savage prompt for {pet_type}: '{prompt[:50]}...'")
        return prompt

    def generate_multiple_prompts(self, count: int = 3, pet_type: str = "general") -> list[str]:
        """Generate multiple unique savage prompts.
        
        Args:
            count: Number of prompts to generate
            pet_type: Type of pet (dog, cat, or general)
            
        Returns:
            List of unique savage roast prompts
        """
        pet_type = pet_type.lower()
        
        if pet_type == "dog":
            source = self.DOG_ROASTS
        elif pet_type == "cat":
            source = self.CAT_ROASTS
        else:
            source = self.all_prompts
        
        # Ensure we don't try to get more prompts than available
        count = min(count, len(source))
        prompts = random.sample(source, count)
        
        _logger.info(f"🔥 Generated {count} savage prompts for {pet_type}")
        return prompts

    def get_prompt_for_context(self, has_audio: bool, pet_type: str = "general") -> str:
        """Get appropriate prompt based on context.
        
        Args:
            has_audio: Whether the video has audio/voice
            pet_type: Type of pet detected
            
        Returns:
            Appropriate savage roast prompt
        """
        if not has_audio:
            _logger.info("🎤 No audio detected, generating savage prompt automatically")
            return self.generate_savage_prompt(pet_type)
        else:
            # This shouldn't be called if audio exists, but return a default just in case
            return "Create an amazing roast video for this adorable pet"


# Singleton instance
_savage_generator = None


def get_savage_prompt_generator() -> SavagePromptGenerator:
    """Get the singleton savage prompt generator instance."""
    global _savage_generator
    if _savage_generator is None:
        _savage_generator = SavagePromptGenerator()
    return _savage_generator
