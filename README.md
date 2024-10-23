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
* text editor to display & edit the state machine in INI format
* graph view to display the state machine in a graphical form

# Summary of cli commands 
                                Welcome to the State Machine CLI
                                ~~~~~~~~~~~~~~~*@*~~~~~~~~~~~~~~

Utility commands
* list: Displays the available state machine JSON files
* load <filname>: Loads a state machine from the specified JSON file
* edit: Edit the states and events of the loaded state machine
* draw_graph: Display the loaded state machine as a graph
* load_two <filename1> <filname2>: Loads two state machines for running concurrently
* quit or exit: Exits the CLI.

State Machine commands
* state: Displays the current state of the loaded state machine
* states: Displays all the states of the loaded state machine
* events: Displays the available transitions from the current state
* history: Displays the states that have been visited
* reset: Returns the state machine to its initial state
* goto <state>: Sets the current state to the named state
* goback <n>: Rewinds the sequence of states by 'n'
* run <event>: Runs an event provided by the you
* run <event1,event2,...>: Runs a sequence of events provided by you
* run --all: Runs all events from the predefined sequence in the JSON file
* run_both: Runs the two loaded state machines concurrently with triggering events passed between them

Logging levels
* INFO: Valid state machine transitions are displayed and stored as INFO logging messages
* ERROR: Invalid state machine transitions are displayed and stored as ERROR logging messages
* WARNING: Missing state machines are displayed and stored as WARNING logging messages





