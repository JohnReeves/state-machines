import argparse
import asyncio
import json
import logging
import os
import cmd

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
    def __init__(self, name, config_file, guard_functions=None):
        self.name = name
        self.config_file = config_file
        self.guard_functions = guard_functions if guard_functions else {}
        self.current_state = None
        self.transition_matrix = None
        self.communications = None
        self.event_sequence = None
        self.load_state_machine()

    def load_state_machine(self):
        """Load the state machine configuration from a JSON file."""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            self.current_state = config["initial_state"]
            self.transition_matrix = config["transitions"]
            self.communications = config.get("communications", {})
            self.event_sequence = config.get("event_sequence", [])  # Load event sequence

    def transition(self, event):
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
            logging.info(f"State machine '{self.name}' transitioned from {old_state} to {self.current_state} on event: {event}")

        else:
            logging.error(f"Invalid transition for state machine '{self.name}' from {self.current_state} with event {event}")

    def run_sequence(self, events):
        """Run a sequence of events for the state machine."""
        logging.info(f"Running event sequence for state machine '{self.name}'")
        for event in events:
            self.transition(event)
            logging.info(f"Event '{event}' processed. Current state: {self.current_state}")

    def run_all(self):
        """Run the predefined sequence of events from the JSON file."""
        if self.event_sequence:
            logging.info(f"Running all events: {', '.join(self.event_sequence)}")
            self.run_sequence(self.event_sequence)
        else:
            logging.warning("No predefined event sequence found.")

# Example of guard functions
def is_system_ready():
    return True

# Helper function to list available JSON files
def list_json_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.json')]

class StateMachineCLI(cmd.Cmd):
    intro = "Welcome to the State Machine CLI. Type help or ? to list commands.\n"
    prompt = "(state-machine) "
    
    def __init__(self, directory, guard_functions=None):
        super().__init__()
        self.directory = directory
        self.guard_functions = guard_functions if guard_functions else {}
        self.machine = None

    def do_list(self, arg):
        """List all available state machine JSON files in the directory. Usage: list"""
        files = list_json_files(self.directory)
        if files:
            logging.info("Available state machine JSON files:")
            for f in files:
                logging.info(f"  - {f}")
        else:
            logging.warning(f"No state machine JSON files found in directory: {self.directory}")
        logging.info(f"Listed available state machine files in {self.directory}")

    def do_load(self, arg):
        """Load a state machine from a JSON file. Usage: load <filename>"""
        try:
            filename = arg.strip()
            if not filename:
                logging.warning("No filename provided. Please provide a valid filename.")
                return
            filepath = os.path.join(self.directory, filename)
            if not os.path.isfile(filepath):
                logging.error(f"File {filename} does not exist in {self.directory}.")
                return
            
            self.machine = StateMachine(filename, filepath, self.guard_functions)
            logging.info(f"State machine '{filename}' loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load state machine: {e}")

    def do_event(self, arg):
        """Send an event to the current state machine. Usage: event <event_name>"""
        if not self.machine:
            logging.warning("No state machine is loaded. Use the 'load' command first.")
            return
        
        event = arg.strip()
        if not event:
            logging.warning("No event provided. Please provide a valid event.")
            return
        
        try:
            self.machine.transition(event)
            logging.info(f"Event '{event}' processed. Current state: {self.machine.current_state}")
        except Exception as e:
            logging.error(f"Failed to process event '{event}': {e}")

    def do_state(self, arg):
        """Display the current state of the loaded state machine. Usage: state"""
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return

        logging.info(f"Current state: {self.machine.current_state}")

    def do_events(self, arg):
        """Show available transitions for the current state. Usage: events"""
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return

        state = self.machine.current_state
        events = list(self.machine.transition_matrix.get(state, {}).keys())
        if events:
            logging.info(f"Available events in state '{state}': {', '.join(events)}")
        else:
            logging.warning(f"No available transitions from state '{state}'.")

    def do_event_sequence(self, arg):
        """List the predefined event sequence from the JSON file. Usage: event_sequence"""
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return
        
        if self.machine.event_sequence:
            logging.info(f"Predefined event sequence: {', '.join(self.machine.event_sequence)}")
        else:
            logging.warning("No predefined event sequence found in the JSON file.")

    def do_states(self, arg):
        """List all states in the loaded state machine. Usage: states"""
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return

        states = list(self.machine.transition_matrix.keys())
        if states:
            logging.info(f"Available states: {', '.join(states)}")
        else:
            logging.warning("No states defined in the state machine.")

    def do_run(self, arg):
        """Run a sequence of events or all events from the JSON file. Usage: run <event1,event2,...> or run --all"""
        if not self.machine:
            logging.warning("No state machine is loaded. Use the 'load' command first.")
            return

        if arg.strip() == "--all":
            try:
                self.machine.run_all()
                logging.info("Ran all events from the JSON event sequence.")
            except Exception as e:
                logging.error(f"Failed to run the event sequence from JSON: {e}")
        else:
            events = arg.strip().split(",")
            if not events:
                logging.warning("No events provided. Please provide a sequence of events to run.")
                return

            try:
                self.machine.run_sequence(events)
                logging.info(f"Ran sequence of events: {', '.join(events)}")
            except Exception as e:
                logging.error(f"Failed to run the event sequence: {e}")

    def do_quit(self, arg):
        """Quit the CLI. Usage: quit"""
        logging.info("Exiting the CLI.")
        return True

    def do_exit(self, arg):
        """Exit the CLI. Usage: exit"""
        return self.do_quit(arg)

def parse_args_and_run_cli():
    parser = argparse.ArgumentParser(description="Run the State Machine CLI to interactively trigger events.")
    
    parser.add_argument(
        "--directory",
        type=str,
        default="./state_machines/",
        help="Directory where state machine JSON files are stored. Default is './state_machines/'"
    )
    
    args = parser.parse_args()
    
    LoggerConfig.setup(log_file="state_machine_cli.log")

    guard_functions = {
        "is_system_ready": is_system_ready
    }

    cli = StateMachineCLI(args.directory, guard_functions)
    cli.cmdloop()

if __name__ == "__main__":
    parse_args_and_run_cli()
