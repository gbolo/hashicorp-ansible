# Nomad and Consul Ansible Modules
This repo contains custom ansible modules I wrote to help facilitate the deployment and maintenance of my platforms that are based on the Hashicorp stack. The modules are designed to idempotent and should always accurately reflect back a change status that occurred during the execution of the module. Some of the modules may also support diff and check (dry-run) modes.

## Installation
**NOTE: Once I get around to creating a collection, the installation will change to a simple `ansible-galaxy collection install` command.**

```
# retrieve the plugin directory from the git repo
❯ git clone https://github.com/gbolo/hashicorp-ansible /tmp/hashicorp-ansible
❯ mv /tmp/hashicorp-ansible/plugins .

# confirm the structure looks something like this
❯ tree plugins
plugins
├── modules
│   ├── consul_acl_bootstrap.py
│   ├── consul_acl_get_token.py
│   ├── consul_acl_policy.py
│   ├── consul_acl_token.py
│   ├── consul_connect_intention.py
│   ├── consul_get_service_detail.py
│   ├── nomad_acl_bootstrap.py
│   ├── nomad_acl_policy.py
│   ├── nomad_acl_token.py
│   ├── nomad_csi_volume.py
│   ├── nomad_job_parse.py
│   ├── nomad_job.py
│   ├── nomad_namespace.py
│   └── nomad_scheduler.py
└── module_utils
    ├── consul.py
    ├── debug.py
    ├── nomad.py
    └── utils.py

# ensure that your ansible.cfg file has these set
❯ cat ansible.cfg
...
library      = ./plugins/modules
module_utils = ./plugins/module_utils
```

## Contributing
The [`Makefile`](Makefile) has targets that help facilitate the development and testing of these modules. This repo uses [pre-commit](https://pre-commit.com/) for git hooks. Most targets require that you have [python-poetry](https://python-poetry.org/) installed. You may also want to install [hashicorp/copywrite](https://github.com/hashicorp/copywrite) to help automate copyright headers.

```
# validate with pre-commit
❯ make pre-commit
poetry run pre-commit run --all-files
check for added large files..............................................Passed
check for case conflicts.................................................Passed
check for broken symlinks............................(no files to check)Skipped
check toml...............................................................Passed
detect private key.......................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
typos....................................................................Passed
black....................................................................Passed
isort....................................................................Passed

# install dev dependencies
❯ make dependency
set -euo pipefail
poetry env info

Virtualenv
Python:         3.10.12
Implementation: CPython
Path:           NA
Executable:     NA

System
Platform:   linux
OS:         posix
Python:     3.10.12
Path:       /usr
Executable: /usr/bin/python3.10
poetry install -n --no-root
Creating virtualenv gbolo-hashicorp-ansible in /home/gbolo/github/hashicorp-ansible/.venv
Installing dependencies from lock file

Package operations: 50 installs, 0 updates, 0 removals

  • Installing attrs (23.1.0)
  • Installing pycparser (2.21)
...

# list molecule test scenarios
❯ make list-tests
set -euo pipefail
cd extensions && poetry run molecule list
WARNING  Driver docker does not provide a schema.
INFO     Running nomad-single > list
INFO     Running nomad_modules > list
                 ╷             ╷                  ╷               ╷         ╷            
  Instance Name  │ Driver Name │ Provisioner Name │ Scenario Name │ Created │ Converged  
╶────────────────┼─────────────┼──────────────────┼───────────────┼─────────┼───────────╴    
  nomad-molecule │ docker      │ ansible          │ nomad_modules │ false   │ false      
                 ╵             ╵                  ╵               ╵         ╵            

# execute module molecule testing
❯ make test-nomad-modules
set -euo pipefail
cd extensions && poetry run molecule list --scenario-name nomad_modules
WARNING  Driver docker does not provide a schema.
INFO     Running nomad_modules > list
                 ╷             ╷                  ╷               ╷         ╷            
  Instance Name  │ Driver Name │ Provisioner Name │ Scenario Name │ Created │ Converged  
╶────────────────┼─────────────┼──────────────────┼───────────────┼─────────┼───────────╴
  nomad-molecule │ docker      │ ansible          │ nomad_modules │ false   │ false      
                 ╵             ╵                  ╵               ╵         ╵            
cd extensions && poetry run molecule converge --scenario-name nomad_modules
WARNING  Driver docker does not provide a schema.
INFO     nomad_modules scenario test matrix: dependency, create, prepare, converge
INFO     Performing prerun with role_name_check=0...
INFO     Running nomad_modules > dependency
Starting galaxy collection install process
Nothing to do. All requested collections are already installed. If you want to reinstall them, consider using `--force`.
INFO     Dependency completed successfully.
WARNING  Skipping, missing the requirements file.
INFO     Running nomad_modules > create
INFO     Sanity checks: 'docker'

PLAY [Create] ******************************************************************

TASK [Set async_dir for HOME env] **********************************************
ok: [localhost]
...
TASK [Delete docker networks(s)] ***********************************************
skipping: [localhost]

PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

INFO     Pruning extra files from scenario ephemeral directory
```