# SAE-SAM

<p align="center">
  <img src="resources/saesam_icon.ico" alt="My Image" width="400"/>
</p>

This software is meant so process the several data from the sonars used in the MIG project autonomous boat:

- Teledyne MB2
- Humminbird Apex

It returns valuable metrics, optimizes files, and point clouds for further studies.

## API logic description

## Dependencies
The program currently relies on Python 3.8, and runs in both Windows and Linux (we recommend Ubuntu 20.04 for python compatibility). Bear in mind that virtual environments may conflict with the GUI execution, so we recommend using everything in the default python interpreter.

To install the project dependencies use the command:

```bash
cd path/to/sae-sam
pip install -r requirements/requirements_python_3_8.txt
```

## Creating the installer
### Windows
We use pyinstaller to generate the executable. Use the following command to create it in the subfolders __build__ and __dist__

```bash
cd path/to/sae-sam
pyinstaller.exe --clean --noconfirm sae-sam.spec
```

Use [this link](https://drive.google.com/file/d/1RaC2BeEg94BblhydD8gZ08M7lKz-mai7/view?usp=drive_link) to download the compressed models that we use in the application. Extract the file content in the project root folder, so that you have __/path/to/sae-sam/models__ structure.

We use inno setup ([download with this link](https://jrsoftware.org/isdl.php#stable)) to generate the installer based on the executable generated in the previous step. The file with the instructions is in the root folder named __installer.iss__. Use it inside inno setup to compile the installer, and optionally run it in your machine to have it installed.

## Running with sample data
