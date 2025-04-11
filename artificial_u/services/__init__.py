"""
Services package for ArtificialU.
Contains modules for different service responsibilities.
"""

from artificial_u.models.database import Repository
from artificial_u.services.voice_service import VoiceService

db_repository = Repository()

# Export pre-initialized service instances
voice_service = VoiceService(repository=db_repository)
