class VoiceSession:

    def __init__(self,mode: int,interview_prompt: str = ""):
        self.mode = mode
        self.messages = []
        if mode == 1:
            self.messages.append(
                {
                    "role": "system",
                    "content": interview_prompt
                }
            )

        self.presentation_transcripts = []

    def add_user_message(self,text: str):
        self.messages.append(
            {
                "role": "user",
                "content": text
            }
        )

    def add_assistant_message(self,text: str):
        self.messages.append(
            {
                "role": "assistant",
                "content": text
            }
        )