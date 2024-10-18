import asyncio
import json
import logging
import os
import argparse


class LoggerConfig:
    @staticmethod
    def setup(log_file="state_machine.log"):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )


class StateMachine:
    def __init__(self, name, config_file, queue, other_machine_queue, guard_functions=None):
        self.name = name
        self.config_file = config_file
        self.queue = queue
        self.other_machine_queue = other_machine_queue
        self.guard_functions = guard_functions if guard_functions else {}
        self.current_state = None
        self.transition_matrix = None
        self.timeout_task = None
        self.timeout_duration = None
        self.load_state_machine()

    def load_state_machine(self):
        """Load the state machine configuration from a JSON file."""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            self.current_state = config["initial_state"]
            self.transition_matrix = config["transitions"]
            self.communications = config.get("communications", {})

    async def transition(self, event):
        """Handles state transitions based on an event."""
        logging.info(f"State machine '{self.name}' received event: {event} in state: {self.current_state}")

        current_transitions = self.transition_matrix.get(self.current_state, {})

        if event in current_transitions:
            transition = current_transitions[event]
            if isinstance(transition, str):
                transition = {"target": transition}

            guard = transition.get("guard")
            if guard:
                guard_func = self.guard_functions.get(guard, None)
                if not guard_func:
                    logging.warning(f"Guard '{guard}' not found for state machine '{self.name}'. Transition blocked.")
                    return
                if not guard_func():
                    logging.warning(f"Guard '{guard}' blocked transition for state machine '{self.name}'")
                    return

            old_state = self.current_state
            self.current_state = transition["target"]
            logging.info(
                f"State machine '{self.name}' transitioned from {old_state} to {self.current_state} on event: {event}")

            if self.timeout_task:
                try:
                    self.timeout_task.cancel()
                except asyncio.CancelledError:
                    logging.info(f"Timeout task for state machine '{self.name}' was already canceled.")
                finally:
                    self.timeout_task = None

            if self.current_state in self.communications:
                comms = self.communications[self.current_state].get(event)
                if comms and self.other_machine_queue:
                    target_event = comms.get("event")
                    if target_event:
                        logging.info(f"State machine '{self.name}' sending event '{target_event}' to other machine.")
                        await self.other_machine_queue.put(target_event)

        else:
            logging.error(
                f"Invalid transition for state machine '{self.name}' from {self.current_state} with event {event}")
            return

    async def run(self):
        """Main loop for the state machine"""
        while True:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=self.timeout_duration)

                if event == "terminate":
                    logging.info(f"State machine '{self.name}' received termination signal. Shutting down.")
                    break  # Exit the loop to terminate the state machine

                await self.transition(event)
            except asyncio.TimeoutError:
                logging.warning(f"Timeout reached in state '{self.current_state}' for state machine '{self.name}'.")
                if "timeout" in self.transition_matrix.get(self.current_state, {}):
                    await self.transition("timeout")
                else:
                    logging.error(
                        f"No timeout transition defined for state '{self.current_state}' in state machine '{self.name}'")
            except Exception as e:
                logging.error(f"Error occurred in state machine '{self.name}': {str(e)}")


# Example of guard functions
def is_system_ready():
    return True

def list_json_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.json')]


async def main():
    """Main function to run state machines in parallel using asyncio."""
    LoggerConfig.setup()

    parser = argparse.ArgumentParser(description="Run two state machines in parallel with communication.")

    parser.add_argument(
        "--state_machine_directory",
        type=str,
        default="./state_machines/",
        help="Directory where state machine JSON files are stored. Default is './state_machines/'"
    )
    parser.add_argument(
        "--file1",
        type=str,
        help="First state machine JSON file. If not provided, the first file found in the directory will be used."
    )
    parser.add_argument(
        "--file2",
        type=str,
        help="Second state machine JSON file. If not provided, the second file found in the directory will be used."
    )

    args = parser.parse_args()

    if not globals().get('state_machine_directory'):
        state_machine_directory = './state_machines/'

    if not globals().get('file1') or not globals().get('file2'):
        available_files = list_json_files(state_machine_directory)

        if len(available_files) < 2:
            logging.error("Need at least two state machine files to run in parallel!")
            return

        file1 = available_files[0]
        file2 = available_files[1]

    logging.info(f"Running state machines: {file1}, {file2}")

    queue1 = asyncio.Queue()
    queue2 = asyncio.Queue()

    guard_functions = {
        "is_system_ready": is_system_ready
    }

    machine1 = StateMachine("machine1", os.path.join(state_machine_directory, file1), queue1, queue2, guard_functions)
    machine2 = StateMachine("machine2", os.path.join(state_machine_directory, file2), queue2, queue1, guard_functions)

    await queue1.put("start")  # Event for machine 1 to start running
    await queue2.put("start")  # Event for machine 2 to start processing

    events = ["up", "stop", "door_open", "door_close", "down", "emergency_trigger", "reset"]
    for e in events:
        await queue1.put(e)

    events = ["insert_money", "select_item", "item_dispensed", "out_of_service", "repair", "insert_money", "cancel"]
    for e in events:
        await queue2.put(e)

    await queue1.put("terminate")
    await queue2.put("terminate")

    await asyncio.gather(machine1.run(), machine2.run())

if __name__ == "__main__":
    asyncio.run(main())