import json
import os

class StateMachine:
    def __init__(self, initial_state, transition_matrix):
        self.current_state = initial_state
        self.transition_matrix = transition_matrix

    def transition(self, event):
        if event in self.transition_matrix.get(self.current_state, {}):
            self.current_state = self.transition_matrix[self.current_state][event]
        else:
            raise ValueError(f"Invalid transition from {self.current_state} with event {event}")

    def get_state(self):
        return self.current_state


def load_transition_matrix(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def list_json_files(directory):
    return [file for file in os.listdir(directory) if file.endswith('.json')]

state_machine_directory = './state_machines/'
available_files = list_json_files(state_machine_directory)

if not available_files:
    print("No state machine files found!")
else:
    print("Available state machines:")
    for idx, file in enumerate(available_files, 1):
        print(f"{idx}. {file}")

    choice = input(f"Choose a state machine by number (1-{len(available_files)}): ").strip()

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(available_files):
            chosen_file = available_files[choice_idx]
            transition_matrix = load_transition_matrix(os.path.join(state_machine_directory, chosen_file))

            if 'elevator' in chosen_file:
                initial_state = 'Idle'
                events = ['up', 'stop', 'door_open', 'door_close', 'down', 'emergency_trigger', 'reset']
            elif 'vending_machine' in chosen_file:
                initial_state = 'Idle'
                events = ['insert_money', 'select_item', 'item_dispensed', 'out_of_service', 'repair', 'cancel']
            else:
                initial_state = 'Idle'
                events = []

            machine = StateMachine(initial_state=initial_state, transition_matrix=transition_matrix)
            print(f"Initial State of {chosen_file}: {machine.get_state()}")

            for event in events:
                try:
                    machine.transition(event)
                    print(f"After event '{event}', Current State: {machine.get_state()}")
                except ValueError as e:
                    print(e)
        else:
            print("Invalid choice! Please select a valid number.")
    except ValueError:
        print("Invalid input! Please enter a number.")
