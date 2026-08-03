To use the following tools first add to ~/.bashrc the location of this repo:

export ROMSTOOLS_ROOT=/path/to/repo

Scripts use this path to locate src code for the code-lab tools that are built ontop of
the [C]Worthy roms-tools repo.

Organization:

/exec
  - Holds configuration files the user made edit for the performance/usage of each tool

/src
  - Respective src code for each of the configuration scripts, stored seperately in src
    for cleanliness and readibility.

Usage:
  - Currently, aliases are the preferred means to call these tools from command line.

    EXAMPLE:
    alias <tool_name>='python3 -i /path/to/exec/directory/script.py'
