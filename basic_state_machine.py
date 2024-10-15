import json

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


state_machines = {
    "elevator": "elevator_transitions.json",
    "vending_machine": "vending_machine_transitions.json"
}

print("Available state machines: ", ", ".join(state_machines.keys()))
choice = input("Which state machine would you like to run? ").strip().lower()

if choice in state_machines:
    transition_matrix = load_transition_matrix(state_machines[choice])
    if choice == "elevator":
        initial_state = 'Idle'  # Elevator starts in Idle state
        events = ['up', 'stop', 'door_open', 'door_close', 'down', 'emergency_trigger', 'reset']
    elif choice == "vending_machine":
        initial_state = 'Idle'  # Vending machine starts in Idle state
        events = ['insert_money', 'select_item', 'item_dispensed', 'out_of_service', 'repair', 'cancel']
    
    machine = StateMachine(initial_state=initial_state, transition_matrix=transition_matrix)
    print(f"Initial State of {choice.capitalize()}: {machine.get_state()}")

    for event in events:
        try:
            machine.transition(event)
            print(f"After event '{event}', Current State: {machine.get_state()}")
        except ValueError as e:
            print(e)
else:
    print("Invalid choice! Please select a valid state machine.")
