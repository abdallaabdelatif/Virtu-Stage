class VoiceSession:

    def __init__(self,system_prompt: str):
        self.messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

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