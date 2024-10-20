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
* load_two <filename1> <filename2>: Loads two state machines for running concurrently
* state: Displays the current state of the loaded state machine
* states: Displays all the states of the loaded state machine
* events: Shows the available transitions from the current state
* reset: Returns the state machine to its initial state
* run <event>: Runs an event provided by the user
* run <event1,event2,...>: Runs a sequence of events provided by the user
* run --all: Runs all events from the predefined sequence in the JSON file
* run_both: Runs the two loaded state machines concurrently with triggering events passed between them
* quit or exit: Exits the CLI.





