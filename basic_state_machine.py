class StateMachine:
    def __init__(self, initial_state, transition_matrix):
        self.current_state = initial_state
        self.transition_matrix = transition_matrix

    def transition(self, event):
        if (self.current_state, event) in self.transition_matrix:
            self.current_state = self.transition_matrix[(self.current_state, event)]
        else:
            raise ValueError(f"Invalid transition from {self.current_state} with event {event}")

    def get_state(self):
        return self.current_state

transition_matrix = {
    ('Idle', 'up'): 'MovingUp',
    ('Idle', 'down'): 'MovingDown',
    ('Idle', 'door_open'): 'DoorOpen',
    ('DoorOpen', 'door_close'): 'Idle',
    
    ('MovingUp', 'stop'): 'Idle',
    ('MovingDown', 'stop'): 'Idle',
    
    ('MovingUp', 'emergency_trigger'): 'Emergency',
    ('MovingDown', 'emergency_trigger'): 'Emergency',
    ('Idle', 'emergency_trigger'): 'Emergency',
    ('DoorOpen', 'emergency_trigger'): 'Emergency',
    
    ('Emergency', 'reset'): 'Idle'
}

elevator = StateMachine(initial_state='Idle', transition_matrix=transition_matrix)
print("Initial State:", elevator.get_state())
events = ['up', 'stop', 'door_open', 'door_close', 'down', 'emergency_trigger', 'reset']

for event in events:
    elevator.transition(event)
    print(f"After event '{event}', Current State:", elevator.get_state())
