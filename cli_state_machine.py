import tkinter as tk
from tkinter import filedialog, messagebox
import configparser
import math

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
        self.current_state = None
        self.transition_matrix = None
        self.communications = None
        self.event_sequence = None
        self.state_history = []
        self.data = {}
        self.guard_functions = guard_functions if guard_functions else {}
        self.load_state_machine()

    def load_state_machine(self):
        """Load the state machine configuration from a JSON file."""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            self.data = config
            self.transition_matrix = config["transitions"]
            self.communications = config.get("communications", {})
            self.event_sequence = config.get("event_sequence", []) 
            self.initial_state = config.get("initial_state", None)  # Store the initial state
            self.state_history = [self.initial_state]
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
            self.state_history.append(old_state)
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
        if state not in self.transition_matrix:
            logging.error(f"State '{state}' does not exist in the state machine '{self.name}'.")
            return

        self.current_state = state
        self.state_history.append(state)
        logging.info(f"State machine '{self.name}' set to state '{state}' using goto command.")

    def goback(self, steps):
        """Revert to an earlier state by the given number of steps."""
        if steps > len(self.state_history)-1:
            logging.warning(f"{len(self.state_history)-1} states available in the history.")
            return

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
        if len(self.event_sequence) == 0:
            logging.warning("No predefined event sequence found.")
            return

        logging.info(f"Running all events: {', '.join(self.event_sequence)}")
        self.run_sequence(self.event_sequence)


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
    edit: Use the embedded text editor to edit the loaded state machine
    draw_graph: Display the loaded state machine as a graph
    load_two <filename1> <filname2>: Loads two state machines for running concurrently
    quit or exit: Exits the CLI.

\033[4mState Machine commands\033[0m
    state: Displays the current state of the loaded state machine
    states: Displays all the states of the loaded state machine
    events: Displays the available transitions from the current state
    history: Displays the states that have been visited
    reset: Returns the state machine to its initial state
    goto <state>: Sets the current state to the named state
    goback <n>: Rewinds the sequence of states by 'n'
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

    def do_draw_graph(self, arg):
        """Draw the loaded state machine as a graph"""
        if self.machine:
            graph = StateMachineGraph(self.machine.data)
            graph.run()
        else:
            print("No state machine loaded. Use 'load <filename>' to load one.")

    def do_edit(self, arg):
        """Open the state machine editor to create or modify a state machine."""
        if self.machine:
            ini_content = self.convert_json_to_ini(self.machine.data)
            editor = StateMachineEditor(self, ini_content) 
        else:
            editor = StateMachineEditor(self)  
        editor.run()

    def convert_json_to_ini(self, json_data):
        """Convert the loaded JSON state machine data into INI format with state subsections."""
        ini_content = []

        # Write the initial state under the [states] section
        if 'states' in json_data and 'initial' in json_data['states']:
            ini_content.append("[states]")
            ini_content.append(f"initial = {json_data['states']['initial']}\n")

        # Write each state's transitions as subsections
        if 'transitions' in json_data:
            for state, events in json_data['transitions'].items():
                ini_content.append(f"[{state}]")
                for event, to_state in events.items():
                    ini_content.append(f"{event} = {to_state}")
                ini_content.append("")  # Blank line for readability

        return "\n".join(ini_content)
    
    def convert_ini_to_json(self, ini_content):
        """Convert INI content with states and subsections for events into JSON format."""
        config = configparser.ConfigParser()
        config.read_string(ini_content)

        state_machine_dict = {
            "states": {},
            "transitions": {}
        }

        # Process the initial state
        if 'states' in config:
            if 'initial' in config['states']:
                state_machine_dict['states']['initial'] = config['states']['initial']

        # Process transitions for each state
        for state in config.sections():
            if state != 'states':  # Ignore the general 'states' section
                transitions = {}
                for event, next_state in config.items(state):
                    transitions[event] = next_state
                state_machine_dict['transitions'][state] = transitions

        return state_machine_dict


    def load_json_state_machine(self, file_path):
        """Load the state machine from the specified JSON file."""
        if not os.path.isfile(file_path):
            logging.error(f"File {file_path} does not exist.")
            return

        with open(file_path, 'r') as json_file:
            state_machine_data = json.load(json_file)
        
        # Load the JSON data into the StateMachine object
        self.machine = StateMachine(os.path.basename(file_path), file_path, self.guard_functions)
        self.machine.data = state_machine_data
        logging.info(f"State machine '{file_path}' loaded successfully.")


    def do_goto(self, arg):
        """Set the state machine directly to a specific state. Usage: goto <state>"""
        if not self.machine:
            logging.warning("No state machine is loaded. Use the 'load' command first.")
            return
        state = arg.strip()
        if not state:
            logging.warning("No state provided. Usage: goto <state>")
            return
        self.machine.goto(state)

    def do_goback(self, arg):
        """Revert the state machine by a number of steps. Usage: goback <n>"""
        if not self.machine:
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

    def do_history(self, arg):
        """Display the current state of the loaded state machine. 
    Usage: state
    """
        if not self.machine:
            logging.warning("No state machine is loaded.")
            return

        logging.info(f"Current history: {self.machine.state_history}")

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




class StateMachineEditor:
    def __init__(self, cli_instance, ini_content=None):
        self.cli_instance = cli_instance
        self.root = tk.Tk()
        self.root.title("State Machine Editor")
        self.root.minsize(30, 800)
        
        # Text widget for editing
        self.text = tk.Text(self.root, wrap=tk.WORD)
        self.text.pack(expand=True, fill=tk.BOTH)
        
        # Pre-populate with the current state machine's INI content if available
        if ini_content:
            self.text.insert(tk.END, ini_content)
        
        # Button Frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Buttons for Load, Save, Edit
        load_button = tk.Button(button_frame, text="Load", command=self.load_ini_file)
        save_button = tk.Button(button_frame, text="Save as JSON", command=self.save_as_json)
        edit_button = tk.Button(button_frame, text="Edit", command=self.edit_state_machine)

        load_button.pack(side=tk.LEFT)
        save_button.pack(side=tk.LEFT)
        edit_button.pack(side=tk.LEFT)

    def load_ini_file(self):
        """Load an INI state machine file into the text editor."""
        file_path = filedialog.askopenfilename(defaultextension=".ini", filetypes=[("INI Files", "*.ini"), ("All Files", "*.*")])
        if not file_path:
            return
        with open(file_path, 'r') as file:
            content = file.read()
            self.text.delete(1.0, tk.END)  # Clear the text widget
            self.text.insert(tk.END, content)  # Insert the INI content
        messagebox.showinfo("Load", f"Loaded {file_path}")

    def save_as_json(self):
        """Save the contents of the text editor in JSON format."""
        content = self.text.get(1.0, tk.END)
        config = configparser.ConfigParser()
        try:
            config.read_string(content)
        except configparser.Error as e:
            messagebox.showerror("Error", f"Failed to parse INI: {str(e)}")
            return
        
        # Convert INI content to JSON format
        state_machine_dict = {section: dict(config.items(section)) for section in config.sections()}
        
        # Save JSON
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not file_path:
            return
        with open(file_path, 'w') as json_file:
            json.dump(state_machine_dict, json_file, indent=4)
        
        messagebox.showinfo("Save", f"Saved as {file_path}")

    def edit_state_machine(self):
        """Load the JSON file into the CLI as a state machine."""
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not file_path:
            return
        
        # Load the JSON file as a state machine in the CLI
        self.cli_instance.load_json_state_machine(file_path)
        messagebox.showinfo("Edit", f"Loaded {file_path} into the state machine")

    def run(self):
        self.root.mainloop()


import tkinter as tk
import math

class StateMachineGraph:
    def __init__(self, json_data):
        self.json_data = json_data
        self.root = tk.Tk()
        self.root.title("State Machine Graph")

        # Canvas for drawing
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Parameters for drawing
        self.state_radius = 40  # Radius for the oval representing a state
        self.states_positions = {}

        self.draw_graph()

    def draw_graph(self):
        """Main function to draw the entire graph."""
        transitions = self.json_data.get('transitions', {})
        states = list(transitions.keys())

        self.position_states_in_circle(states)

        for state, (x, y) in self.states_positions.items():
            self.draw_state_oval(x, y, state)

        for from_state, events in transitions.items():
            from_x, from_y = self.states_positions[from_state]
            for event, to_state in events.items():
                to_x, to_y = self.states_positions[to_state]
                self.draw_transition(from_x, from_y, to_x, to_y, event)

    def position_states_in_circle(self, states):
        """Position states in a circle for a basic layout."""
        center_x, center_y = 400, 300  # Center of the canvas
        radius = 200 

        num_states = len(states)
        angle_step = 2 * math.pi / num_states

        for i, state in enumerate(states):
            angle = i * angle_step
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.states_positions[state] = (x, y)

    def draw_state_oval(self, x, y, state_name):
        """Draw an oval for the state and place its name in the center."""
        r = self.state_radius
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="lightblue", outline="black")
        self.canvas.create_text(x, y, text=state_name, font=("Arial", 14))

    def draw_transition(self, from_x, from_y, to_x, to_y, event_name):
        """Draw a line with an arrow from one state to another, labeled with an event."""
        self.canvas.create_line(from_x, from_y, to_x, to_y, arrow=tk.LAST, fill="black")

        mid_x = (from_x + to_x) / 2
        mid_y = (from_y + to_y) / 2
        self.canvas.create_text(mid_x, mid_y - 10, text=event_name, font=("Arial", 10, "italic"))

    def run(self):
        self.root.mainloop()


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
