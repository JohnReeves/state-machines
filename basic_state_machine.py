import json
import os
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("state_machine.log"),
                        logging.StreamHandler()
                    ])

class StateMachine:
    def __init__(self, initial_state, transition_matrix):
        self.current_state = initial_state
        self.transition_matrix = transition_matrix

    def transition(self, event):
        logging.info(f"Received event: {event} in state: {self.current_state}")
        
        if event in self.transition_matrix.get(self.current_state, {}):
            old_state = self.current_state
            self.current_state = self.transition_matrix[self.current_state][event]
            logging.info(f"Transitioned from {old_state} to {self.current_state} on event: {event}")
        else:
            logging.error(f"Invalid transition from {self.current_state} with event {event}")
            raise ValueError(f"Invalid transition from {self.current_state} with event {event}")

    def get_state(self):
        return self.current_state


def load_state_machine(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    initial_state = data["initial_state"]
    events = data["events"]
    transitions = data["transitions"]
    return initial_state, events, transitions


def list_json_files(directory):
    return [file for file in os.listdir(directory) if file.endswith('.json')]


state_machine_directory = './state_machines/'
available_files = list_json_files(state_machine_directory)

if not available_files:
    logging.error("No state machine files found!")
else:
    print("Available state machines:")
    for idx, file in enumerate(available_files, 1):
        print(f"{idx}. {file}")

    choice = input(f"Choose a state machine by number (1-{len(available_files)}): ").strip()

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(available_files):
            chosen_file = available_files[choice_idx]
            logging.info(f"User selected state machine file: {chosen_file}")

            initial_state, events, transition_matrix = load_state_machine(os.path.join(state_machine_directory, chosen_file))
            machine = StateMachine(initial_state=initial_state, transition_matrix=transition_matrix)

            logging.info(f"Initial State: {machine.get_state()}")

            for event in events:
                try:
                    machine.transition(event)
                except ValueError as e:
                    logging.error(e)
        else:
            logging.error("Invalid choice! Please select a valid number.")
    except ValueError:
        logging.error("Invalid input! Please enter a number.")

