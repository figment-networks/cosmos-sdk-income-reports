class __Settings():
    def __init__(self):
        self.configure({
            'debug': False,
        })

    def configure(self, settings):
        for k, v in settings.items():
            setattr(self, k, v)


settings = __Settings()
