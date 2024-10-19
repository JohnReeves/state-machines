# state-machines

assumes a directory structure
```
 /state-machine/
    basic_state_machine.py
    robust_state_machine.py
    cli_state_machine.py
    /state_machines/
        elevator_transitions.json
        vending_machine_transitions.json
        etc.json
```

`basic_state_machine.py` has
* json file transition matrix
* logging to the screen and to a file
* argparse selection of directory and files

`robust_state_machine.py` has
* as above
* robustness to errors in state machine files
* logs an error and waits for the next input event

`cli_state_machine.py` has
* as above
* cmd user interface

# Summary of cli commands 
* list: Lists available state machine JSON files
* load <filename>: Loads a state machine from the specified JSON file
* event <event_name>: Triggers an event for the loaded state machine
* state: Displays the current state of the loaded state machine
* states: Displays all the states of the loaded state machine
* events: Shows the available transitions from the current state
* event_sequence: Lists the predefined event sequence from the JSON file
* run <event1,event2,...>: Runs a sequence of events provided by the user
* run --all: Runs all events from the predefined sequence in the JSON file
* quit or exit: Exits the CLI.
