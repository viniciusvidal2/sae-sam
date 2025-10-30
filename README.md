# SAE-SAM

<p align="center">
  <img src="resources/saesam_icon.ico" alt="My Image" width="400"/>
</p>

This software is meant so process the several data from the sonars used in the MIG project autonomous boat:

- Teledyne MB2
- Humminbird Apex

It returns valuable metrics, optimizes files, and point clouds for further studies.

## API logic description
The program has the following executables:

- Apex DAT processor: reads the DAT files from Apex sonar. They are recorded in the SD card, which is removed after the mission. The data is read and several manipulation tools are available to deal with the waterfall imagery
- Apex images processor: detects items that are blocking the grid by semantic type, and returns its area and volume. It uses images collected by the Apex sonar
- MB2 files optimizer: uses the Pixhawk embedded board logs and the original HSX files (plus other project files) to optimize the HSX GPS readings, creating a much cleaner point cloud output
- SAESC - SAE Scene Creator: merges point clouds obtained with both sonar and drone images. Processes them to have the readings in UTM coordinates, filtered and positioned in the world frame

In the backend, this is the structure we used to organized the API calls:
- windows: windows and the libs we need to contain each executable
- workers: classes to call the processing pipelines in a separate thread, organized by the windows
- modules: the actual processing classes, with the intelligence (optimizations, AI modules, among others) of the project
- pingmapper: minimalist version of the pingmapper open-source code to perform waterfall image extraction from Apex recorded data, in the formats of .DAT, .SON, and .IDX

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
Get the sample data from [this link](https://drive.google.com/file/d/1jRpBirL8HIHAnxdEPSyt4a75Oe41vize/view?usp=drive_link). Use it in this way:

- Apex DAR processor: use the __Rec00005.DAT__ (inside apex_dat_rec subfolder) and create a project output folder to obtain the processed images as results.
- Apex images processor: insert the __demo_image.jpg__ and hit process
- MB2 files optimizer: use __0000_1714_0002.HSX__ and __2024-10-31 15-58-52.bin__ files and hit the processing or view buttons. When ready, click download to have the outputs.
- SAESC - SAE Scene Creator: Use __22_12_2023.xyz__ (sonar) and __espigao.ply__ (drone) by adding clouds. Click process, visualize and download the output.
