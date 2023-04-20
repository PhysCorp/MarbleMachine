# MarbleMachine
### A small utility to convert either an image or a whiteboard drawing (via camera) into a 2D G-Code line drawing.

## Notes
Tested on Fedora 37

## Todo
- [ ] X

## Requirements
- [x] Python 3.6
- [x] python3-pip
- [x] conda
- [ ] python3-virtualenv

## Installation
1. Install python3, python3-pip and anaconda. Anaconda can be retrieved from [here](https://www.anaconda.com/products/individual). If you are on Windows, you can install anaconda with [chocolatey](https://chocolatey.org/) using `choco install anaconda3`.
2. Create a conda environment with `conda create --name MarbleMachine python=3.6`.
3. Activate the conda environment with `conda activate MarbleMachine`.
4. Install the requirements with `python3 -m pip install -r requirements.txt`.

## Usage
0. Download this project with `git clone https://github.com/PhysCorp/MarbleMachine.git`
1. Activate the conda environment with `conda activate MarbleMachine`.
2. Run `python3 main.py` to start the program. Here is an example command:
```python3 main.py input="FULL_PATH_TO_IMAGE.png" bed_shake=False output="FULL_PATH_TO_OUTPUT.stl"```

### Alternate Instructions using virtualenv
Create a new virtualenv with `python3 -m venv venv`.
Activate the virtualenv with `source venv/bin/activate`.
Install the requirements with `python3 -m pip install -r requirements.txt`.

## Uninstall
1. Deactivate the conda environment with `conda deactivate`.
2. Remove the conda environment with `conda remove --name MarbleMachine --all`.