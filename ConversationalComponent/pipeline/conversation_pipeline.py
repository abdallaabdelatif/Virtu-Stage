from interfaces.llm_service import ILLMService
from interfaces.tts_service import ITTSService
from pipeline.voice_session import VoiceSession


class ConversationPipeline:

    def __init__(self,llm: ILLMService,tts: ITTSService):
        self.llm = llm
        self.tts = tts

    async def process_transcript(self,session: VoiceSession,transcript: str):
        session.add_user_message(transcript)
        response = await self.llm.generate_response(session.messages)
        session.add_assistant_message(response)
        return response