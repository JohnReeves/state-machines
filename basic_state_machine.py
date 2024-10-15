class StateMachine:
    def __init__(self, initial_state, transition_matrix):
        self.current_state = initial_state
        self.transition_matrix = transition_matrix

    def transition(self, event):
        # Get the next state based on the current state and the event
        if (self.current_state, event) in self.transition_matrix:
            self.current_state = self.transition_matrix[(self.current_state, event)]
        else:
            raise ValueError(f"Invalid transition from {self.current_state} with event {event}")

    def get_state(self):
        return self.current_state

transition_matrix = {
    ('Red', 'timer_expired'): 'Green',
    ('Green', 'timer_expired'): 'Yellow',
    ('Yellow', 'timer_expired'): 'Red'
}

traffic_light = StateMachine(initial_state='Red', transition_matrix=transition_matrix)
print("Initial State:", traffic_light.get_state())
events = ['timer_expired', 'timer_expired', 'timer_expired', 'timer_expired']

for event in events:
    traffic_light.transition(event)
    print("Current State:", traffic_light.get_state())
