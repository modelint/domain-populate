# Blueprint Domain Populator

This package takes three inputs, a populated metamodel database, a context and a yaml file mapping user to system types.

### Populated metamodel database

This is a metamodel TclRAL database (*.ral) file populated with a user's domain model: the Elevator Management domain populated into the Shlaer-Mellor metamodel, for example. It is probably named `elevator_mmdb.ral`

This *.ral file is produced by the modeldb command if you have the xuml-populate package installed.

### Context

A scenario instance population *.sip file that you write yourself which specifies instances and current states to be populated into your domain database. This file defines a context that can be used in a variety of simulation scenarios in a downstream package currently under development called model execute.

### Type Mapping

A yaml file that maps each domain type to a TclRAL system type.

## Command usage

`% domaindb -s elevator.ral -c EVMAN_one_bank1.sip -t EVMAN_types.yaml`

Here -s is the system, -c is the context, and -t specifies the mapping of domain types to available system
data types which currently are TclRAL types.