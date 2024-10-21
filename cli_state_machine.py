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
            self.transition_matrix = config["transitions"]
            self.communications = config.get("communications", {})
            self.event_sequence = config.get("event_sequence", []) 
            self.initial_state = config.get("initial_state", None)  # Store the initial state
            self.current_state = config["initial_state"]

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
 
    def reset(self):
        """Reset the state machine to its initial state."""
        self.current_state = self.initial_state
        logging.info(f"State machine '{self.name}' reset to initial state '{self.initial_state}'.")

    def goto(self, state):
        """Set the current state directly to a specified state."""
        if state in self.transition_matrix:
            self.current_state = state
            self.state_history.append(state)  # Append the new state to history
            logging.info(f"State machine '{self.name}' set to state '{state}' using goto command.")
        else:
            logging.error(f"State '{state}' does not exist in the state machine '{self.name}'.")

    def goback(self, steps):
        """Revert to an earlier state by the given number of steps."""
        if steps >= len(self.state_history):
            logging.warning(f"Cannot go back {steps} steps. Reverting to initial state.")
            self.current_state = self.initial_state
            self.state_history = [self.initial_state]
        else:
            # Revert by popping the history and setting the current state
            self.current_state = self.state_history[-(steps + 1)]
            self.state_history = self.state_history[:-(steps)]
            logging.info(f"Reverted state machine '{self.name}' back by {steps} steps to state '{self.current_state}'.")

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
    intro = """
    
                                Welcome to the State Machine CLI
                                ~~~~~~~~~~~~~~~*@*~~~~~~~~~~~~~~

\033[4mUtility commands\033[0m
    list: Displays the available state machine JSON files
    load <filname>: Loads a state machine from the specified JSON file
    load_two <filename1> <filname2>: Loads two state machines for running concurrently
    quit or exit: Exits the CLI.

\033[4mState Machine commands\033[0m
    state: Displays the current state of the loaded state machine
    states: Displays all the states of the loaded state machine
    events: Displays the available transitions from the current state
    reset: Returns the state machine to its initial state
    run <event>: Runs an event provided by the you
    run <event1,event2,...>: Runs a sequence of events provided by you
    run --all: Runs all events from the predefined sequence in the JSON file
    run_both: Runs the two loaded state machines concurrently with triggering events passed between them

\033[4mLogging levels\033[0m
    INFO: Valid state machine transitions are displayed and stored as INFO logging messages
    ERROR: Invalid state machine transitions are displayed and stored as ERROR logging messages
    WARNING: Missing state machines are displayed and stored as WARNING logging messages

                                Welcome to the State Machine CLI
                                ~~~~~~~~~~~~~~~*@*~~~~~~~~~~~~~~

\033[4mWhile using the State Machine CLI\033[0m
    Type 'help' or '?' to list all the available commands
    Type 'help <command>' to get a reminder of <command>'s syntax

    """
    prompt = "(state-machine) "
    
    def __init__(self, directory, guard_functions=None):
        super().__init__()
        self.directory = directory
        self.guard_functions = guard_functions if guard_functions else {}
        self.machine = None
        self.machine1 = None
        self.machine2 = None

    def do_list(self, arg):
        """List all available state machine JSON files in the directory. 
    Usage: list
    """
        files = list_json_files(self.directory)
        if files:
            logging.info("Available state machine JSON files:")
            for f in files:
                logging.info(f"  - {f}")
        else:
            logging.warning(f"No state machine JSON files found in directory: {self.directory}")
        logging.info(f"Listed available state machine files in {self.directory}")

    def do_load(self, arg):
        """Load a single state machine from a JSON file. 
    Usage: load <filename>
    """
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

    def do_goto(self, arg):
        """Set the state machine directly to a specific state. Usage: goto <state>"""
        if not self.machine1:
            logging.warning("No state machine is loaded. Use the 'load' command first.")
            return
        state = arg.strip()
        if not state:
            logging.warning("No state provided. Usage: goto <state>")
            return
        self.machine.goto(state)

    def do_goback(self, arg):
        """Revert the state machine by a number of steps. Usage: goback <n>"""
        if not self.machine1:
            logging.warning("No state machine is loaded. Use the 'load' command first.")
            return
        try:
            steps = int(arg)
        except ValueError:
            logging.error("Please provide a valid number for goback.")
            return
        self.machine.goback(steps)

    def do_state(self, arg):
        """Display the current state of the loaded state machine. 
    Usage: state
    """
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return

        logging.info(f"Current state: {self.machine.current_state}")

    def do_events(self, arg):
        """Show available transitions for the current state. 
    Usage: events
    """
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return

        state = self.machine.current_state
        events = list(self.machine.transition_matrix.get(state, {}).keys())
        if events:
            logging.info(f"Available events in state '{state}': {', '.join(events)}")
        else:
            logging.warning(f"No available transitions from state '{state}'.")

    def do_states(self, arg):
        """List all states in the loaded state machine. 
    Usage: states
    """
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return

        states = list(self.machine.transition_matrix.keys())
        if states:
            logging.info(f"Available states: {', '.join(states)}")
        else:
            logging.warning("No states defined in the state machine.")

    def do_run(self, arg):
        """Run an event, a sequence of events or all events from the JSON file. 
    Usage: 
    run <event>
    run <event1,event2,...> or 
    run --all
    """
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

    def do_reset(self, arg):
        """Reset the currently loaded state machine to its initial state. Usage: reset"""
        if not self.machine:
            logging.warning("No state machine is loaded. Use the 'load' command first.")
            return
        
        self.machine.reset()

    def do_load_two(self, arg):
        """Load two state machines from JSON files. 
    Usage: 
    load_two <filename1> <filename2>
    """
        filenames = arg.strip().split()
        if len(filenames) != 2:
            logging.warning("Please provide two filenames. Usage: load_two <filename1> <filename2>")
            return
        
        filepath1 = os.path.join(self.directory, filenames[0])
        filepath2 = os.path.join(self.directory, filenames[1])

        if not os.path.isfile(filepath1) or not os.path.isfile(filepath2):
            logging.error(f"One or both files do not exist: {filenames[0]}, {filenames[1]}")
            return
        
        self.machine1 = StateMachine(filenames[0], filepath1, self.guard_functions)
        self.machine2 = StateMachine(filenames[1], filepath2, self.guard_functions)
        logging.info(f"State machines '{filenames[0]}' and '{filenames[1]}' loaded successfully.")
    
    def do_run_both(self, arg):
        """Run two state machines concurrently and pass events between them. 
    Usage: run_both
    """
        if not self.machine1 or not self.machine2:
            logging.warning("Both state machines need to be loaded. Use 'load_two' to load two state machines.")
            return
        
        logging.info("Starting to run both state machines concurrently.")
        
        asyncio.run(self.run_both_machines())

    async def run_both_machines(self):
        """Run both state machines concurrently and allow them to communicate."""
        task1 = asyncio.create_task(self.run_machine(self.machine1))
        task2 = asyncio.create_task(self.run_machine(self.machine2))
        
        # Run both tasks concurrently
        await asyncio.gather(task1, task2)

    async def run_machine(self, machine):
        """Run a single state machine with asyncio."""
        logging.info(f"Running state machine {machine.name}")
        
        for event in machine.event_sequence:
            await asyncio.sleep(1)  # Simulate delay between events
            logging.info(f"Processing event {event} in {machine.name}")
            machine.transition(event)
            
            # Check if an event should trigger another event in the other machine
            if machine == self.machine1 and event == "trigger_machine2_event":
                logging.info("Triggering event in machine 2 from machine 1.")
                await self.run_event_in_machine(self.machine2, "event_from_machine1")
            elif machine == self.machine2 and event == "trigger_machine1_event":
                logging.info("Triggering event in machine 1 from machine 2.")
                await self.run_event_in_machine(self.machine1, "event_from_machine2")

    async def run_event_in_machine(self, machine, event):
        """Run a specific event in a state machine asynchronously."""
        await asyncio.sleep(0.5)  # Simulate small delay
        logging.info(f"Running event {event} in {machine.name}")
        machine.transition(event)

    def do_quit(self, arg):
        """Quit the CLI. 
    Usage: quit
    """
        logging.info("Exiting the CLI.")
        return True

    def do_exit(self, arg):
        """Exit the CLI. 
    Usage: exit
    """
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
