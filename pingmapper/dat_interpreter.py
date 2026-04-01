import os
import json
import time
import datetime
import numpy as np
import cv2
import shutil
from typing import Generator
from pingmapper.main_readFiles import read_master_func
from modules.path_tool import get_file_placement_path


class DatInterpreter:
    def __init__(self) -> None:
        """Class constructor"""
        # Initialize default parameters
        self.default_params_file = get_file_placement_path(
            'pingmapper/default_params.json')
        self.params = self._generate_default_params(
            params_file=self.default_params_file)
        # The project path and wether to keep raw data or not
        self.output_project_path = None
        self.keep_raw_data = True
        # DAT and respective SON and IDX paths
        self.dat_file_path = None
        self.son_idx_subfolder_path = None
        # Output merged images paths
        self.merged_high_freq_path = None
        self.merged_very_high_freq_path = None

    def _generate_default_params(self, params_file: str) -> dict:
        """
        Generate the default parameters and adapt the necessary fields so we only get the waterfall images

        Args:
            params_file (str): Path to the parameters file

        Returns:
            dict: The generated default parameters
        """
        with open(params_file, 'r') as f:
            params = json.load(f)
        params.pop('inDir', None)  # Remove inDir if exists
        params.pop('filter_table', None)  # Remove inDir if exists
        params['project_mode'] = 1  # 0==NEW PROJECT; 1==OVERWRITE MODE
        params['egn'] = False
        # "Percent Clip", "Min-Max" or "None"
        params['egn_stretch'] = "Percent Clip"
        params['egn_stretch_factor'] = 0.5
        params['wcp'] = True
        params['wcm'] = False
        params['wcr'] = False
        params['rect_wcp'] = False
        params['rect_wcr'] = False
        params['sonogram_colorMap'] = 'copper'
        params['son_colorMap'] = 'copper'
        params['pred_sub'] = False
        # EGN Stretch
        egn_stretch = params['egn_stretch']
        if egn_stretch == 'None':
            params['egn_stretch'] = 0
        elif egn_stretch == 'Min-Max':
            params['egn_stretch'] = 1
        elif egn_stretch == 'Percent Clip':
            params['egn_stretch'] = 2
        # Depth detection
        detectDep = params['detectDep']
        if detectDep == 'Sensor':
            params['detectDep'] = 0
        elif detectDep == 'Auto':
            params['detectDep'] = 1
        # Shadow removal
        remShadow = params['remShadow']
        if remShadow == 'False':
            params['remShadow'] = 0
        elif remShadow == 'Remove all shadows':
            params['remShadow'] = 1
        elif remShadow == 'Remove only bank shadows':
            params['remShadow'] = 2
        # Sonar mosaic
        mosaic = params['mosaic']
        if mosaic == 'False':
            params['mosaic'] = int(0)
        elif mosaic == 'GTiff':
            params['mosaic'] = int(1)
        elif mosaic == 'VRT':
            params['mosaic'] = int(2)
        # Substrate mosaic
        map_mosaic = params['map_mosaic']
        if map_mosaic == 'False':
            params['map_mosaic'] = 0
        elif map_mosaic == 'GTiff':
            params['map_mosaic'] = 1
        elif map_mosaic == 'VRT':
            params['map_mosaic'] = 2
        # Return the modified parameters
        return params

    def set_dat_path(self, p: str) -> None:
        """Set the DAT file path

        Args:
            p (str): The DAT file path
        """
        self.dat_file_path = p

    def set_son_idx_subfolder_path(self, p: str) -> None:
        """Set the SON/IDX subfolder path

        Args:
            p (str): The SON/IDX subfolder path
        """
        self.son_idx_subfolder_path = p

    def set_project_path(self, p: str) -> None:
        """Set the project output path

        Args:
            p (str): The project output path
        """
        self.output_project_path = p

    def set_keep_raw_data(self, keep: bool) -> None:
        """Set whether to keep raw data after processing.

        Args:
            keep (bool): True to keep raw data, False to delete it after processing.
        """
        self.keep_raw_data = keep

    def generate_waterfall_images(self) -> Generator[str, None, None]:
        """Generate the waterfall images from the DAT file
        Yields a string with the status and the result of the process, which can be emitted to the GUI log output

        Yields:
            str: Status and result messages during the processing of the DAT file and generation of waterfall images
        """
        if not self.output_project_path:
            yield "No project output path set."
        if not self.dat_file_path:
            yield "No DAT file path set."
        if not self.son_idx_subfolder_path:
            yield "No SON/IDX subfolder path set."
        # Set the former parameters from the paths
        sonFiles = [os.path.join(self.son_idx_subfolder_path, f) for f in sorted(
            os.listdir(self.son_idx_subfolder_path)) if f.endswith('.SON')]
        logfilename = os.path.join(
            self.output_project_path, 'log_'+time.strftime("%Y-%m-%d_%H%M")+'.txt')
        copied_script_name = "not_used"
        script = "not_used"
        self.params['projDir'] = self.output_project_path
        self.params['inFile'] = self.dat_file_path
        self.params['sonFiles'] = sonFiles
        self.params['logfilename'] = logfilename
        self.params['script'] = [script, copied_script_name]

        # Try to acquire the images from the DAT and SON files, and save them in the project path
        start_time = time.time()
        try:
            yield "Reading the DAT file content..."
            # Generate image tiles
            read_master_func(**self.params)
            yield "Image tiles generated successfully form DAT file. Now merging them into complete waterfall images..."
            
            # Merge and save waterfall images
            merged = self._merge_save_waterfall_images()
            yield f"Merging and saving waterfall images process result: {'Success' if merged else 'Failed'}"
            if not merged:
                yield "Error during merging and saving waterfall images."
            
            # Clean temporary files in the project folder
            if not self.keep_raw_data:
                yield "Cleaning temporary files in the project folder..."
                self._clean_project_folder()
                yield "Temporary files cleaned successfully."
            else:
                yield "Keeping raw data as per user selection. Skipping cleaning of temporary files."
            # Return success message with processing time
            process_time = datetime.timedelta(
                seconds=round(time.time() - start_time, ndigits=0))
            yield f"Waterfall images generated successfully in {self.output_project_path}.\nTotal Processing Time: {process_time}"
        except Exception as Argument:
            yield f"Error during processing: {str(Argument)}"

    def _merge_save_waterfall_images(self) -> bool:
        """Merge and save the waterfall images

        Returns:
            bool: True if successful, False otherwise
        """
        # Subfolders in project folder
        if not self.output_project_path:
            return False
        high_freq_folder = os.path.join(
            self.output_project_path, "ds_highfreq", "wcp")
        very_high_freq_folder = os.path.join(
            self.output_project_path, "ds_vhighfreq", "wcp")
        
        # Instead of failing if one of them is missing, let's gracefully handle what we have
        high_freq_files = []
        very_high_freq_files = []
        
        if os.path.exists(high_freq_folder):
            high_freq_files = sorted(
                [f for f in os.listdir(high_freq_folder) if f.endswith('.png')])
        
        if os.path.exists(very_high_freq_folder):
            very_high_freq_files = sorted(
                [f for f in os.listdir(very_high_freq_folder) if f.endswith('.png')])
            
        if not high_freq_files and not very_high_freq_files:
            return False
        high_freq_image = None
        if high_freq_files:
            high_freq_image = self._merge_image_tiles(
                image_files_list=high_freq_files, folder=high_freq_folder)
                
        very_high_freq_image = None
        if very_high_freq_files:
            very_high_freq_image = self._merge_image_tiles(
                image_files_list=very_high_freq_files, folder=very_high_freq_folder)

        # Get the part that is not background based on brightness
        bottom_foreground_row = None
        if very_high_freq_image is not None:
            bottom_foreground_row = self._find_background_region(
                image=very_high_freq_image)
        elif high_freq_image is not None:
            bottom_foreground_row = self._find_background_region(
                image=high_freq_image)

        # Crop both images
        if bottom_foreground_row is not None:
            if high_freq_image is not None:
                high_freq_image = high_freq_image[:bottom_foreground_row, :]
            if very_high_freq_image is not None:
                very_high_freq_image = very_high_freq_image[:bottom_foreground_row, :]

        # Save merged images
        self.merged_high_freq_path = None
        self.merged_very_high_freq_path = None
        
        if high_freq_image is not None:
            self.merged_high_freq_path = os.path.join(
                self.output_project_path, "highfreq_image_merged.png")
            cv2.imwrite(self.merged_high_freq_path, high_freq_image)
            
        if very_high_freq_image is not None:
            self.merged_very_high_freq_path = os.path.join(
                self.output_project_path, "very_highfreq_image_merged.png")
            cv2.imwrite(self.merged_very_high_freq_path, very_high_freq_image)

        return True

    def _merge_image_tiles(self, image_files_list: list, folder: str) -> np.ndarray:
        """
        Merge image tiles into a single image

        Args:
            image_files_list (list): List of image paths to merge
            folder (str): Folder where the image files are located

        Returns:
            np.ndarray: Merged image array
        """
        # Read every image and get the one with the lowest height
        min_height = float('inf')
        images = []
        for img_file in image_files_list:
            img = cv2.imread(os.path.join(folder, img_file))
            images.append(img)
            if img.shape[0] < min_height:
                min_height = img.shape[0]
        # Resize images to the minimum height and concatenate vertically
        resized_images = [cv2.resize(
            img, (img.shape[1], min_height)) for img in images]
        merged_image = cv2.hconcat(resized_images)
        return merged_image

    def _clean_project_folder(self) -> None:
        """Clean temporary files in the project folder"""
        # Folders to remove, independently if they are empty or not
        temp_folders = ['ds_highfreq', 'ds_vhighfreq', 'unknown',
                        'meta', 'processing_scripts',
                        'ss_star', 'ss_port']
        for folder in temp_folders:
            folder_path = os.path.join(
                self.output_project_path, folder)
            if os.path.exists(folder_path):
                try:
                    # Remove the folder and its contents
                    shutil.rmtree(folder_path)
                except Exception as e:
                    print(f"Error removing folder {folder_path}: {str(e)}")

    def get_merged_images_paths(self) -> dict:
        """Get the paths of the merged waterfall images

        Returns:
            dict: Dictionary with paths to merged high frequency and very high frequency images
        """
        return {
            'highfreq_image_merged': self.merged_high_freq_path,
            'very_highfreq_image_merged': self.merged_very_high_freq_path
        }

    def _find_background_region(self, image: np.ndarray) -> int:
        """
        Find a background region in the given image based on a brightness threshold.

        Args:
            image (np.ndarray): The input image in which to find the background region.

        Returns:
            int: The bottom row coordinate where the background should start.
        """
        # convert to grayscale if image is colored
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image
        # Get the bottom section of the image, maybe a third of the height
        height = gray_image.shape[0]
        bottom_section = gray_image[int(height*2/3):, :]
        # Calculate the mean and standard deviation of the bottom section
        mean_brightness = np.mean(bottom_section)
        std_brightness = np.std(bottom_section)
        # Define a brightness threshold to identify background pixels
        brightness_threshold = mean_brightness + std_brightness
        # Go every thickness lines in the image from this bottom up, calculating the percentage of pixels below the threshold
        thickness = 50  # pixels
        for row in range(gray_image.shape[0] - bottom_section.shape[0], int(gray_image.shape[0] / 4) - thickness + 1, -thickness):
            line_region = gray_image[row - thickness:row, :]
            line_region_mean = np.mean(line_region)
            if line_region_mean > brightness_threshold:
                return row - thickness
        # If no suitable region found, return half the image height
        return int(gray_image.shape[0] / 2)


if __name__ == "__main__":
    pass
