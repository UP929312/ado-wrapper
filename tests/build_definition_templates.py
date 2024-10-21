MOST_BASIC_BUILD_YAML_FILE = """---
trigger: none

pool:
  vmImage: ubuntu-latest

steps:
  - script: echo Hello, world!
    displayName: 'Run a one-line script'
"""

MULTIPLE_STAGES_BUILD_YAML_FILE = """
trigger: none

pool:
  vmImage: ubuntu-latest

stages:
- stage: StageOne
  displayName: StageOne
  jobs:
  - job: JobOne
    displayName: JobOne
    steps:
    - script: echo Hello, world!
      displayName: 'Task1'

- stage: StageTwo
  dependsOn: []
  displayName: StageTwo
  jobs:
  - job: JobTwo
    displayName: JobTwo
    steps:
    - script: echo Hello, world 2!
      displayName: 'Task2'"""

MULTIPLE_STAGES_WITH_DEPENDENCIES_BUILD_YAML_FILE = """
trigger: none

pool:
  vmImage: ubuntu-latest

stages:
- stage: StageOne
  displayName: StageOne
  jobs:
  - job: JobOne
    displayName: JobOne
    steps:
    - script: echo Hello, world!
      displayName: 'Task1'

- stage: StageTwo
  displayName: StageTwo
  jobs:
  - job: JobTwo
    displayName: JobTwo
    steps:
    - script: echo Hello, world 2!
      displayName: 'Task2'"""

TEMPLATE_PARAMS_YAML_FILE = """
trigger: none

pool:
  vmImage: ubuntu-latest

parameters:
  - name: toggle
    displayName: "Which stages to run"
    type: string
    default: stage1
    values:
      - stage1
      - stage2

stages:
  - ${{ if eq(parameters.toggle, 'stage1') }}:
      - stage: Stage1
        displayName: "Stage 1"
        jobs:
          - job: Job1
            steps:
              - bash: |
                  echo "Stage 1"
                displayName: Echo Stage 1

  - ${{ if eq(parameters.toggle, 'stage2') }}:
      - stage: Stage2
        displayName: "Stage 2"
        jobs:
          - job: Job2
            steps:
              - bash: |
                  echo "Stage 2"
                displayName: Echo Stage 2

"""

TEMPLATE_VARIABLES_YAML_FILE = """
trigger: none

pool:
  vmImage: ubuntu-latest

variables:
- name: my_var
  value: aaa
  readonly: false

stages:
  - stage: Stage1
    jobs:
      - job: Job1
        steps:
          - bash: |
              echo "Pipeline variable value: $(my_var)"
            displayName: "Print Pipeline Variable"
"""

INTEGRATIONS_TEST_YAML_FILE = """---
trigger:
  - main

pool:
  vmImage: ubuntu-latest

variables:
  - group: ado_wrapper-test-for-integrations

steps:
  - script: echo Hello, world!
    displayName: 'Integrations Testing'"""
