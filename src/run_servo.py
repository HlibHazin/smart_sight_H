import time

from servo import ServoWorker
from statemanger import StateManager


servo_worker = ServoWorker()
state_manager = StateManager()

while True:
    if state_manager.exit:
        break
    servo_worker.update(
        state_manager.yaw,
        state_manager.pitch,
        state_manager.signal_duration_ms,
        state_manager.pause_duration_ms
    )
    time.sleep(0.1)

state_manager.join()
