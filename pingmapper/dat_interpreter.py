import os
import json
import time
import datetime
from pingmapper.main_readFiles import read_master_func
from modules.path_tool import get_file_placement_path


class DatInterpreter:
    def __init__(self):
        """Class constructor"""
        # Initialize default parameters
        self.default_params_file = get_file_placement_path(
            'pingmapper/default_params.json')
        self.params = self._generate_default_params(
            params_file=self.default_params_file)
        # The project path
        self.output_project_path = None
        # DAT and respective SON and IDX paths
        self.dat_file_path = None
        self.son_idx_subfolder_path = None

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

    def generate_waterfall_images(self) -> str:
        """Generate the waterfall images from the DAT file"""
        if not self.output_project_path:
            return "No project output path set."
        if not self.dat_file_path:
            return "No DAT file path set."
        if not self.son_idx_subfolder_path:
            return "No SON/IDX subfolder path set."
        # Set the former parameters from the paths
        sonFiles = [os.path.join(self.son_idx_subfolder_path, f) for f in sorted(
            os.listdir(self.son_idx_subfolder_path)) if f.endswith('.SON')]
        logfilename = os.path.join(
            self.output_project_path, 'log_'+time.strftime("%Y-%m-%d_%H%M")+'.txt')
        copied_script_name = os.path.basename(__file__).split(
            '.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
        script = os.path.abspath(__file__)
        self.params['projDir'] = self.output_project_path
        self.params['inFile'] = self.dat_file_path
        self.params['sonFiles'] = sonFiles
        self.params['logfilename'] = logfilename
        self.params['script'] = [script, copied_script_name]

        # Try to acquire the images from the DAT and SON files, and save them in the project path
        start_time = time.time()
        try:
            read_master_func(**self.params)
            process_time = datetime.timedelta(
                seconds=round(time.time() - start_time, ndigits=0))
            return f"Waterfall images generated successfully in {self.output_project_path}.\nTotal Processing Time: {process_time}"
        except Exception as Argument:
            return f"Error during processing: {str(Argument)}"

    def get_image_root_path(self):
        pass
