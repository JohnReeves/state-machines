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

with open('transitions.json', 'r') as f:
    transition_matrix = json.load(f)

elevator = StateMachine(initial_state='Idle', transition_matrix=transition_matrix)
print("Initial State:", elevator.get_state())
events = ['up', 'stop', 'door_open', 'door_close', 'down', 'emergency_trigger', 'reset']

for event in events:
    try:
        elevator.transition(event)
        print(f"After event '{event}', Current State:", elevator.get_state())
    except ValueError as e:
        print(e)
