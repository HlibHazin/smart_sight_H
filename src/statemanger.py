from pynput.keyboard import Key, Listener

from servo import ServoCommands


def stub():
    pass


class StateManager:
    def __init__(self, on_enter=None):
        self.yaw = ServoCommands.STOP
        self.pitch = ServoCommands.STOP

        self.manual_mode = True
        self.exit = False
        self.laser = False

        self.listener = Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

        if on_enter is None:
            on_enter = stub
        self.on_enter = on_enter

    def _on_press(self, key):
        if key == Key.esc:
            self.exit = True

            self.yaw = ServoCommands.STOP
            self.pitch = ServoCommands.STOP

            return False

        if hasattr(key, "char") and key.char is not None:
            char = key.char.upper()
            if char in {"M", "Ь"}:
                self.manual_mode = not self.manual_mode
                self.yaw = ServoCommands.STOP
                self.pitch = ServoCommands.STOP

            if char in {"L", "Д"}:
                self.laser = not self.laser
                if self.laser:
                    self.yaw = ServoCommands.LASER_ON
                else:
                    self.yaw = ServoCommands.LASER_OFF
                self.pitch = ServoCommands.IGNORE

            if self.manual_mode:
                if char in {"W", "Ц"}:
                    self.pitch = ServoCommands.DEC
                if char in {"S", "Ы"}:
                    self.pitch = ServoCommands.INC
                if char in {"A", "Ф"}:
                    self.yaw = ServoCommands.DEC
                if char in {"D", "В"}:
                    self.yaw = ServoCommands.INC

        if self.manual_mode:
            if key == Key.up:
                self.pitch = ServoCommands.DEC
            if key == Key.down:
                self.pitch = ServoCommands.INC
            if key == Key.left:
                self.yaw = ServoCommands.DEC
            if key == Key.right:
                self.yaw = ServoCommands.INC
            if key == Key.enter:
                self.on_enter()

    def _on_release(self, key):
        if self.manual_mode:
            if key == Key.up or (hasattr(key, "char") and key.char is not None and key.char.upper() in {"W", "Ц", "S", "Ы"}):
                self.pitch = ServoCommands.STOP
            if key == Key.down or (hasattr(key, "char") and key.char is not None and key.char.upper() in {"W", "Ц", "S", "Ы"}):
                self.pitch = ServoCommands.STOP
            if key == Key.left or (hasattr(key, "char") and key.char is not None and key.char.upper() in {"A", "Ф", "D", "В"}):
                self.yaw = ServoCommands.STOP
            if key == Key.right or (hasattr(key, "char") and key.char is not None and key.char.upper() in {"A", "Ф", "D", "В"}):
                self.yaw = ServoCommands.STOP

    def join(self):
        self.listener.stop()

    def is_camera_moving(self) -> bool:
        return self.yaw != ServoCommands.STOP or self.pitch != ServoCommands.STOP
