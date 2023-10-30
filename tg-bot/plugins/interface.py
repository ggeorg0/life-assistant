class MorningMsgPlugin:
    _enabled: bool
    _name: str

    def __init__(self) -> None:
        self._enabled = True
        self._name = "defaultpluginname"

    def process_message(self, message: list[str]):
        if self.enabled:
            return self._process_message(message)

    def _process_message(self, message: list[str]):
        raise NotImplementedError("Subclasses must implement this method")
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value