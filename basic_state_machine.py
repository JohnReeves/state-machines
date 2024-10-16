import os
import logging
import json
import asyncio
from typing import Dict, Callable

class LoggerConfig:
    """A class to configure logging for the application."""
    
    @staticmethod
    def setup(log_file="state_machine.log", log_level=logging.INFO):
        """Configures logging to output to both a file and the console."""
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

def is_system_ready() -> bool:
    """Example guard function that checks if the system is ready for a transition."""
    return True  # For demonstration, always return True. This could be based on real conditions.

class StateMachine:
    def __init__(self, name, file_path, event_queue, other_machine_queue=None, guard_functions: Dict[str, Callable] = None):
        self.name = name
        self.event_queue = event_queue
        self.other_machine_queue = other_machine_queue
        self.guard_functions = guard_functions or {}
        self.timeout_task = None
        self.load_state_machine(file_path)

    def load_state_machine(self, file_path):
        """Loads the state machine configuration from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.current_state = data["initial_state"]
        self.events = data["events"]
        self.transition_matrix = data["transitions"]
        self.communications = data.get("communications", {})

        logging.info(f"State machine '{self.name}' loaded. Initial State: {self.current_state}")

    async def run(self):
        """Run the state machine asynchronously."""
        while True:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=self.get_state_timeout())
            except asyncio.TimeoutError:
                # Handle timeout transition
                await self.handle_timeout()
                continue

            if event == "STOP":
                logging.info(f"State machine '{self.name}' is stopping.")
                break

            await self.transition(event)

    async def handle_timeout(self):
        """Handles the timeout event and performs a transition if defined."""
        current_transitions = self.transition_matrix.get(self.current_state, {})
        for event, transition in current_transitions.items():
            if "timeout" in transition:
                logging.info(f"State machine '{self.name}' transitioning due to timeout in state '{self.current_state}'")
                await self.transition(event)
                return

    def get_state_timeout(self):
        """Returns the timeout for the current state, or None if no timeout is set."""
        current_transitions = self.transition_matrix.get(self.current_state, {})
        for event, transition in current_transitions.items():
            if "timeout" in transition:
                return transition["timeout"]
        return None

    async def transition(self, event):
        """Handles state transitions based on an event."""
        logging.info(f"State machine '{self.name}' received event: {event} in state: {self.current_state}")
        
        current_transitions = self.transition_matrix.get(self.current_state, {})
        
        if event in current_transitions:
            transition = current_transitions[event]
            
            guard = transition.get("guard")
            if guard and not self.guard_functions.get(guard, lambda: False)():
                logging.warning(f"Guard '{guard}' blocked transition for state machine '{self.name}'")
                return
            
            old_state = self.current_state
            self.current_state = transition["target"]
            logging.info(f"State machine '{self.name}' transitioned from {old_state} to {self.current_state} on event: {event}")
            
            if self.timeout_task:
                self.timeout_task.cancel()
                self.timeout_task = None
            
            if self.current_state in self.communications:
                comms = self.communications[self.current_state].get(event)
                if comms and self.other_machine_queue:
                    target_event = comms.get("event")
                    if target_event:
                        logging.info(f"State machine '{self.name}' sending event '{target_event}' to other machine.")
                        await self.other_machine_queue.put(target_event)
        else:
            logging.error(f"Invalid transition for state machine '{self.name}' from {self.current_state} with event {event}")
            raise ValueError(f"Invalid transition for state machine '{self.name}' from {self.current_state} with event {event}")

def list_json_files(directory):
    """Lists all JSON files in the specified directory."""
    return [file for file in os.listdir(directory) if file.endswith('.json')]

async def main():
    """Main function to run state machines in parallel using asyncio."""
    LoggerConfig.setup()

    state_machine_directory = './state_machines/'
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

    await queue1.put("start") 
    await queue2.put("start_other")  

    # Later, add pause, resume, finish, and error events to simulate various scenarios
    await asyncio.sleep(5)
    await queue1.put("pause") 
    await asyncio.sleep(2)
    await queue1.put("resume")  
    await asyncio.sleep(3)
    await queue1.put("finish")  
    await asyncio.sleep(4)
    await queue2.put("complete")  

    await asyncio.gather(machine1.run(), machine2.run())

if __name__ == "__main__":
    asyncio.run(main())
