import os
import logging
import argparse
import json

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

class StateMachine:
    def __init__(self, file_path):
        self.load_state_machine(file_path)

    def load_state_machine(self, file_path):
        """Loads the state machine configuration from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.current_state = data["initial_state"]
        self.events = data["events"]
        self.transition_matrix = data["transitions"]

        logging.info(f"State machine loaded. Initial State: {self.current_state}")

    def transition(self, event):
        """Handles state transitions based on an event."""
        logging.info(f"Received event: {event} in state: {self.current_state}")

        if event in self.transition_matrix.get(self.current_state, {}):
            old_state = self.current_state
            self.current_state = self.transition_matrix[self.current_state][event]
            logging.info(f"Transitioned from {old_state} to {self.current_state} on event: {event}")
        else:
            logging.error(f"Invalid transition from {self.current_state} with event {event}")
            raise ValueError(f"Invalid transition from {self.current_state} with event {event}")

    def get_state(self):
        """Returns the current state of the state machine."""
        return self.current_state


def list_json_files(directory):
    """Lists all JSON files in the specified directory."""
    return [file for file in os.listdir(directory) if file.endswith('.json')]


def main():
    """Main function for executing the state machine program."""
    LoggerConfig.setup()

    parser = argparse.ArgumentParser(description="Run a state machine from a JSON file.")
    parser.add_argument('--directory', 
                        type=str, 
                        default='./state_machines/', 
                        help='Directory where state machine JSON files are stored (default: ./state_machines/)')
    parser.add_argument('--file', 
                        type=str, 
                        help='The JSON file to use for the state machine.')

    args = parser.parse_args()

    state_machine_directory = args.directory

    if not args.file:
        available_files = list_json_files(state_machine_directory)

        if not available_files:
            logging.error("No state machine files found!")
            return

        print("Available state machines:")
        for idx, file in enumerate(available_files, 1):
            print(f"{idx}. {file}")

        choice = input(f"Choose a state machine by number (1-{len(available_files)}): ").strip()

        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(available_files):
                chosen_file = available_files[choice_idx]
            else:
                logging.error("Invalid choice! Please select a valid number.")
                return
        except ValueError:
            logging.error("Invalid input! Please enter a number.")
            return
    else:
        chosen_file = args.file

    logging.info(f"User selected state machine file: {chosen_file}")

    machine = StateMachine(file_path=os.path.join(state_machine_directory, chosen_file))

    for event in machine.events:
        try:
            machine.transition(event)
        except ValueError as e:
            logging.error(e)

if __name__ == "__main__":
    main()
