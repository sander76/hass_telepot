class MockBot:
    def __init__(self):
        self.handle = None

    def glance(self, message):
        pass

    def message_loop(self, call_back):
        self.handle = call_back

    def sendMessage(self, chat_id, text, **kwargs):
        self.chat_id = chat_id
        self.text = text
