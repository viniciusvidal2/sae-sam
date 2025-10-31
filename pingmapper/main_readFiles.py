# Part of PING-Mapper software
#
# GitHub: https://github.com/CameronBodine/PINGMapper
# Website: https://cameronbodine.github.io/PINGMapper/
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2025 Cameron S. Bodine
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import contextlib
import copy
from pingverter import hum2pingmapper
import os
import sys
import time
import pandas as pd
from pingmapper.funcs_common import *
from pingmapper.class_sonObj import sonObj
import shutil


class DevNull:
    def write(self, msg):
        pass

    def flush(self):
        pass


sys.stdout = DevNull()
sys.stderr = DevNull()

# ===========================================


def read_master_func(logfilename='',
                     project_mode=0,
                     script='',
                     inFile='',
                     sonFiles='',
                     projDir='',
                     coverage=False,
                     aoi=False,
                     max_heading_deviation=False,
                     max_heading_distance=False,
                     min_speed=False,
                     max_speed=False,
                     time_table=False,
                     tempC=10,
                     nchunk=500,
                     cropRange=0,
                     exportUnknown=False,
                     fixNoDat=False,
                     threadCnt=0,
                     pix_res_son=0,
                     pix_res_map=0,
                     x_offset=0,
                     y_offset=0,
                     tileFile='.png',
                     egn=False,
                     egn_stretch=0,
                     egn_stretch_factor=1,
                     wcp=False,
                     wcm=False,
                     wcr=False,
                     wco=False,
                     sonogram_colorMap='Greys_r',
                     mask_shdw=False,
                     mask_wc=False,
                     spdCor=False,
                     maxCrop=False,
                     moving_window=False,
                     window_stride=0.1,
                     USE_GPU=False,
                     remShadow=0,
                     detectDep=0,
                     smthDep=0,
                     adjDep=0,
                     pltBedPick=False,
                     rect_wcp=False,
                     rect_wcr=False,
                     rubberSheeting=True,
                     rectMethod='COG',
                     rectInterpDist=50,
                     son_colorMap='Greys',
                     pred_sub=0,
                     map_sub=0,
                     export_poly=False,
                     map_predict=0,
                     pltSubClass=False,
                     map_class_method='max',
                     mosaic_nchunk=50,
                     mosaic=False,
                     map_mosaic=0,
                     banklines=False):
    '''
    Main script to read data from Humminbird sonar recordings. Scripts have been
    tested on 9xx, 11xx, Helix, Solix and Onyx models but should work with any
    Humminbird model (updated July 2021).

    ----------
    Parameters
    ----------
    sonFiles : str
        DESCRIPTION - Path to .SON file directory associated w/ .DAT file.
        EXAMPLE -     sonFiles = 'C:/PINGMapper/SonarRecordings/R00001'
    humFile : str
        DESCRIPTION - Path to .DAT file associated w/ .SON directory.
        EXAMPLE -     humFile = 'C:/PINGMapper/SonarRecordings/R00001.DAT'
    projDir : str
        DESCRIPTION - Path to output directory.
        EXAMPLE -     projDir = 'C:/PINGMapper/procData/R00001'
    tempC : float : [Default=10]
        DESCRIPTION - Water temperature (Celcius) during survey.
        EXAMPLE -     tempC = 10
    nchunk : int : [Default=500]
        DESCRIPTION - Number of pings per chunk.  Chunk size dictates size of
                      sonar tiles (sonograms).  Most testing has been on chunk
                      sizes of 500 (recommended).
        EXAMPLE -     nchunk = 500
    exportUnknown : bool [Default=False]
        DESCRIPTION - Flag indicating if unknown attributes in ping
                      should be exported or not.  If a user of PING Mapper
                      determines what an unkown attribute actually is, please
                      report using a github issue.
        EXAMPLE -     exportUnknown = False
    wcp : bool : [Default=False]
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      present (wcp).
                      True = export wcp sonar tiles;
                      False = do not export wcp sonar tiles.
        EXAMPLE -     wcp = True
    wcr : bool : [Default=False]
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      removed (wcr).
                      True = export wcr sonar tiles;
                      False = do not export wcr sonar tiles.
        EXAMPLE -     wcr = True
    detectDep : int : [Default=0]
        DESCRIPTION - Determines if depth will be automatically estimated for
                      water column removal.
                      0 = use Humminbird depth;
                      1 = auto pick using Zheng et al. 2021;
                      2 = auto pick using binary thresholding.
       EXAMPLE -     detectDep = 0
    smthDep : bool : [Default=False]
        DESCRIPTION - Apply Savitzky-Golay filter to depth data.  May help smooth
                      noisy depth estimations.  Recommended if using Humminbird
                      depth to remove water column (detectDep=0).
                      True = smooth depth estimate;
                      False = do not smooth depth estimate.
        EXAMPLE -     smthDep = False
    adjDep : int : [Default=0]
        DESCRIPTION - Specify additional depth adjustment (in pixels) for water
                      column removal.  Does not affect the depth estimate stored
                      in exported metadata *.CSV files.
                      Integer > 0 = increase depth estimate by x pixels.
                      Integer < 0 = decrease depth estimate by x pixels.
                      0 = use depth estimate with no adjustment.
        EXAMPLE -     adjDep = 5
    pltBedPick : bool : [Default=False]
        DESCRIPTION - Plot bedpick(s) on non-rectified sonogram for visual
                      inspection.
                      True = plot bedpick(s);
                      False = do not plot bedpick(s).
        EXAMPLE -     pltBedPick = True
    threadCnt : int : [Default=0]
        DESCRIPTION - The maximum number of threads to use during multithreaded
                      processing. More threads==faster data export.
                      0 = Use all available threads;
                      <0 = Negative values will be subtracted from total available
                        threads. i.e., -2 -> Total threads (8) - 2 == 6 threads.
                      >0 = Number of threads to use, up to total available threads.
        EXAMPLE -     threadCnt = 0

    -------
    Returns
    -------
    Project directory with following structure and outputs, pending parameter
    selection:

    |--projDir
    |
    |--|ds_highfreq (if B001.SON available) [wcp=True]
    |  |--wcp
    |     |--*.PNG : Down-looking sonar (ds) 200 kHz sonar tiles (non-rectified),
    |     |          w/ water column present
    |
    |--|ds_lowfreq (if B000.SON available) [wcp=True]
    |  |--wcp
    |     |--*.PNG : Down-looking sonar (ds) 83 kHz sonar tiles (non-rectified),
    |     |          w/ water column present
    |
    |--|ds_vhighfreq (if B004.SON available) [wcp=True]
    |  |--wcp
    |     |--*.PNG : Down-looking sonar (ds) 1.2 mHz sonar tiles (non-rectified),
    |     |          w/ water column present
    |
    |--|meta
    |  |--B000_ds_lowfreq_meta.csv : ping metadata for B000.SON (if present)
    |  |--B000_ds_lowfreq_meta.meta : Pickled sonObj instance for B000.SON (if present)
    |  |--B001_ds_highfreq_meta.csv : ping metadata for B001.SON (if present)
    |  |--B001_ds_highfreq_meta.meta : Pickled sonObj instance for B001.SON (if present)
    |  |--B002_ss_port_meta.csv : ping metadata for B002.SON (if present)
    |  |--B002_ss_port_meta.meta : Pickled sonObj instance for B002.SON (if present)
    |  |--B003_ss_star_meta.csv : ping metadata for B003.SON (if present)
    |  |--B003_ss_star_meta.meta : Pickled sonObj instance for B003.SON (if present)
    |  |--B004_ds_vhighfreq.csv : ping metadata for B004.SON (if present)
    |  |--B004_ds_vhighfreq.meta : Pickled sonObj instance for B004.SON (if present)
    |  |--DAT_meta.csv : Sonar recording metadata for *.DAT.
    |
    |--|ss_port (if B002.SON OR B003.SON [tranducer flipped] available)
    |  |--wcr [wxr=True]
    |     |--*.PNG : Portside side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column removed (wcr) & slant range corrected
    |  |--wcp [wcp=True]
    |     |--*.PNG : Portside side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column present (wcp)

    |--|ss_star (if B003.SON OR B002.SON [tranducer flipped] available)
    |  |--wcr [wcr=True]
    |     |--*.PNG : Starboard side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column removed (wcr) & slant range corrected
    |  |--wcp [wcp=True]
    |     |--*.PNG : Starboard side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column present (wcp)
    '''

    #####################################
    # Show version
    from pingmapper.version import __version__

    threadCnt = 1

    #######################################
    # Use PINGVerter to read the sonar file
    #######################################
    instDepAvail = True
    start_time = time.time()
    # Determine sonar recording type
    _, file_type = os.path.splitext(inFile)
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        sonar_obj = hum2pingmapper(
            inFile, projDir, nchunk, tempC, exportUnknown)

    ####################
    # Create son objects
    ####################
    # Get available beams and metadata
    beamMeta = sonar_obj.beamMeta

    # Create son objects
    sonObjs = []
    for beam, meta in beamMeta.items():
        # Create the sonObj
        son = sonObj(meta['sonFile'], sonar_obj.humFile,
                     projDir, sonar_obj.tempC, sonar_obj.nchunk)

        son.flip_port = False
        if beam == 'B002':
            if file_type == '.sl2' or file_type == '.sl3':
                son.flip_port = True

        # Store other parameters as attributes
        son.fixNotDat = fixNoDat
        son.metaDir = sonar_obj.metaDir
        son.beamName = meta['beamName']
        son.beam = beam
        son.headBytes = sonar_obj.headBytes
        son.isOnix = sonar_obj.isOnix
        son.trans = sonar_obj.trans
        son.humDat = sonar_obj.humDat
        son.son8bit = sonar_obj.son8bit
        son.export_beam = True

        if pix_res_son == 0:
            son.pix_res_son = 0
        else:
            son.pix_res_son = pix_res_son
        if pix_res_map == 0:
            son.pix_res_map = 0
        else:
            son.pix_res_map = pix_res_map

        son.sonMetaFile = meta['metaCSV']

        if sonFiles:
            if any(son.beam in s for s in sonFiles):
                sonObjs.append(son)

    # Both port and starboard are required for side scan workflows
    # Make copy of ss if both aren't available
    ss_dups = {
        'ss_port': ['ss_star', 'B003'],
        'ss_star': ['ss_port', 'B002']
    }
    ss_chan_avail = []
    for son in sonObjs:
        if son.beamName == 'ss_port' or son.beamName == 'ss_star':
            ss_chan_avail.append(son)
    if len(ss_chan_avail) == 0:
        max_heading_deviation = 0
        min_speed = 0
        max_speed = 0
        aoi = ''
        time_table = ''
        detectDep = 0
        pltBedPick = False
        remShadow = 0
        pred_sub = False
        egn = False
        wco = False
        wcm = False
    elif len(ss_chan_avail) == 1:
        origBeam = son.beamName
        son_copy = copy.deepcopy(ss_chan_avail[0])
        son_copy.beamName = ss_dups[origBeam][0]
        son_copy.beam = ss_dups[origBeam][1]
        son_copy.export_beam = False
        # Make copy of meta file
        oldMeta = son.sonMetaFile
        newMeta = '{}_{}_meta_copy.csv'.format(
            son_copy.beam, son_copy.beamName)
        newMeta = os.path.join(os.path.dirname(oldMeta), newMeta)
        shutil.copy(oldMeta, newMeta)
        son_copy.sonMetaFile = newMeta
        son_copy.outDir = os.path.join(
            os.path.dirname(oldMeta), son_copy.beamName)
        sonObjs.append(son_copy)

    ############################################################################
    # Decode DAT file (varies by model)                                        #
    ############################################################################

    if (project_mode != 2):
        # Store cropRange in object
        for son in sonObjs:
            son.cropRange = cropRange

        # Store flag to export un-rectified sonar tiles in each sonObj.
        for son in sonObjs:
            beam = son.beamName
            son.wcp = wcp
            son.wco = wco
            son.wcm = wcm
            if wcr:
                if beam == "ss_port" or beam == "ss_star":
                    son.wcr_src = True
                else:
                    son.wcr_src = False
            else:
                son.wcr_src = False
            del beam
        del son
    ############################################################################
    # Locating missing pings                                                   #
    ############################################################################

    if fixNoDat:
        # Open each beam df, store beam name in new field, then concatenate df's into one
        frames = []
        for son in sonObjs:
            son._loadSonMeta()
            df = son.sonMetaDF
            df['beam'] = son.beam
            frames.append(df)
            son._cleanup()
            del df

        dfAll = pd.concat(frames)
        del frames
        # Sort by record_num
        dfAll = dfAll.sort_values(by=['record_num'], ignore_index=True)
        dfAll = dfAll.reset_index(drop=True)
        beams = dfAll['beam'].unique()

        # 'Evenly' allocate work to process threads.
        # Future: Add workflow to balance workload (histogram). Determine total 'missing' pings
        # and divide by processors, then subsample until workload is balanced
        rowCnt = len(dfAll)
        rowsToProc = []
        c = 0
        r = 0
        n = int(rowCnt/threadCnt)
        startB = dfAll.iloc[0]['beam']

        while (r < threadCnt) and (n < rowCnt):
            if (dfAll.loc[n]['beam']) != startB:
                n += 1
            else:
                rowsToProc.append((c, n))
                c = n
                n = c+int(rowCnt/threadCnt)
                r += 1
        rowsToProc.append((rowsToProc[-1][-1], rowCnt))
        del c, r, n, startB, rowCnt

        r = [son._fixNoDat(dfAll[r[0]:r[1]].copy().reset_index(
            drop=True), beams) for r in rowsToProc]
        gc.collect()

        # Concatenate results from parallel processing
        dfAll = pd.concat(r)
        del r

        # Store original record_num and update record_num with new index
        dfAll = dfAll.sort_values(by=['record_num'], ignore_index=True)
        dfAll['orig_record_num'] = dfAll['record_num']
        dfAll['record_num'] = dfAll.index

        # Slice dfAll by beam, update chunk_id, then save to file.
        for son in sonObjs:
            df = dfAll[dfAll['beam'] == son.beam]

            if (len(df) % nchunk) != 0:
                rdr = nchunk-(len(df) % nchunk)
                chunkCnt = int(len(df)/nchunk)
                chunkCnt += 1
            else:
                rdr = False
                chunkCnt = int(len(df)/nchunk)

            chunks = np.arange(chunkCnt)
            chunks = np.repeat(chunks, nchunk)
            del chunkCnt

            if rdr:
                chunks = chunks[:-rdr]

            df['chunk_id'] = chunks

            # Make sure last chunk is long enough
            c = df['chunk_id'].max()  # Get last chunk value
            lastChunk = df[df['chunk_id'] == c]  # Get last chunk rows
            if len(lastChunk) <= (nchunk/2):
                df.loc[df['chunk_id'] == c, 'chunk_id'] = c-1

            df.drop(columns=['beam'], inplace=True)

            # Check that last chunk has index anywhere in the chunk.
            # If not, a bunch of NoData was added to the end.
            # Trim off the NoData
            maxIdx = df[['index']].idxmax().values[0]
            maxIdxChunk = df.at[maxIdx, 'chunk_id']
            maxChunk = df['chunk_id'].max()

            if maxIdxChunk <= maxChunk:
                df = df[df['chunk_id'] <= maxIdxChunk]

            # son._saveSonMetaCSV(df)
            son._cleanup()
        del df, rowsToProc, dfAll, son, chunks, rdr, beams

    else:
        if project_mode != 2:
            for son in sonObjs:
                son.fixNoDat = fixNoDat

    for son in sonObjs:
        son._pickleSon()

    ############################################################################
    # For Filtering                                                            #
    ############################################################################

    # Determine which sonObj is port/star
    portstar = []
    for son in sonObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            portstar.append(son)

    # Create portstarObj
    # psObj = portstarObj(portstar)

    chunks = []
    for son in portstar:
        # Get chunk id's, ignoring those with nodata
        c = son._getChunkID()

        chunks.extend(c)
        del c
    del son

    chunks = np.unique(chunks).astype(int)

    # Don't estimate depth, use instrument depth estimate (sonar derived)
    if detectDep == 0:
        autoBed = False
        saveDepth = True
    else:
        saveDepth = False

    # Cleanup
    # psObj._cleanup()
    # del psObj, portstar
    del portstar

    for son in sonObjs:
        son._cleanup()
        son._pickleSon()
    del son

    ############################################################################
    # For shadow removal                                                       #
    ############################################################################
    # Use deep learning segmentation algorithms to automatically detect shadows.
    # 1: Remove all shadows (those cause by boulders/objects)
    # 2: Remove only contiguous shadows touching max range extent. May be
    # useful for locating river banks...

    for son in sonObjs:
        son.remShadow = 0

    for son in sonObjs:
        son._pickleSon()

    # Cleanup
    try:
        # psObj._cleanup()
        # del psObj, portstar
        del portstar
    except:
        pass

    ############################################################################
    # For sonar intensity corrections/normalization                            #
    ############################################################################

    if egn:
        start_time = time.time()
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                son.egn = True
                son.egn_stretch = egn_stretch

                # Determine what chunks to process
                chunks = son._getChunkID()
                chunks = chunks[:-1]  # remove last chunk

                # Load sonMetaDF
                son._loadSonMeta()

                chunk_means = [son._egnCalcChunkMeans(i) for i in chunks]

                # Calculate global means
                son._egnCalcGlobalMeans(chunk_means)
                del chunk_means

                min_max = [son._egnCalcMinMax(i) for i in chunks]

                # Calculate global min max for each channel
                son._egnCalcGlobalMinMax(min_max)
                del min_max

                son._cleanup()
                son._pickleSon()

                gc.collect()

            else:
                son.egn = False  # Dont bother with down-facing beams

        # Get true global min and max

        bed_mins = []
        bed_maxs = []
        wc_mins = []
        wc_maxs = []
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                bed_mins.append(son.egn_bed_min)
                bed_maxs.append(son.egn_bed_max)
                wc_mins.append(son.egn_wc_min)
                wc_maxs.append(son.egn_wc_max)
        bed_min = np.min(bed_mins)
        bed_max = np.max(bed_maxs)
        wc_min = np.min(wc_mins)
        wc_max = np.max(wc_maxs)
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                son.egn_bed_min = bed_min
                son.egn_bed_max = bed_max
                son.egn_wc_min = wc_min
                son.egn_wc_max = wc_max

            # Tidy up
            son._cleanup()
            son._pickleSon()
            gc.collect()

        # Need to calculate histogram if egn_stretch is greater then 0
        if egn_stretch > 0:
            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    # Determine what chunks to process
                    chunks = son._getChunkID()
                    chunks = chunks[:-1]  # remove last chunk
                    hist = [son._egnCalcHist(i) for i in chunks]
                    son._egnCalcGlobalHist(hist)

            # Now calculate true global histogram
            egn_wcp_hist = np.zeros((255))
            egn_wcr_hist = np.zeros((255))

            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    egn_wcp_hist += son.egn_wcp_hist
                    egn_wcr_hist += son.egn_wcr_hist

            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    son.egn_wcp_hist = egn_wcp_hist
                    son.egn_wcr_hist = egn_wcr_hist

            # Calculate global percentages and standard deviation
            wcp_pcnt = np.zeros((egn_wcp_hist.shape))
            wcr_pcnt = np.zeros((egn_wcr_hist.shape))

            # Calculate total pixels
            wcp_sum = np.sum(egn_wcp_hist)
            wcr_sum = np.sum(egn_wcr_hist)

            # Caclulate percentages
            for i, v in enumerate(egn_wcp_hist):
                wcp_pcnt[i] = egn_wcp_hist[i] / wcp_sum

            for i, v in enumerate(egn_wcr_hist):
                wcr_pcnt[i] = egn_wcr_hist[i] / wcr_sum

            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    son.egn_wcp_hist_pcnt = wcp_pcnt
                    son.egn_wcr_hist_pcnt = wcr_pcnt

            del egn_wcp_hist, egn_wcr_hist, wcp_pcnt, wcr_pcnt
            # del egn_wcr_hist, wcr_pcnt

            # Calculate min and max for rescale
            for son in sonObjs:
                if son.beamName == 'ss_port':
                    wcp_stretch, wcr_stretch = son._egnCalcStretch(
                        egn_stretch, egn_stretch_factor)
                    # wcr_stretch = son._egnCalcStretch(egn_stretch, egn_stretch_factor)

                    # Tidy up
                    son._cleanup()
                    son._pickleSon()
                    gc.collect()

            for son in sonObjs:
                if son.beamName == 'ss_star':
                    son.egn_stretch = egn_stretch
                    son.egn_stretch_factor = egn_stretch_factor

                    son.egn_wcp_stretch_min = wcp_stretch[0]
                    son.egn_wcp_stretch_max = wcp_stretch[1]

                    son.egn_wcr_stretch_min = wcr_stretch[0]
                    son.egn_wcr_stretch_max = wcr_stretch[1]

                    # Tidy up
                    son._cleanup()
                    son._pickleSon()
                    gc.collect()
    else:
        if project_mode != 2:
            for son in sonObjs:
                son.egn = False

    ############################################################################
    # Export un-rectified sonar tiles                                          #
    ############################################################################

    imgType = tileFile
    if wcp or wcr or wco or wcm:
        start_time = time.time()
        for son in sonObjs:
            if (son.wcp or son.wcr_src or son.wco or son.wcm) and son.export_beam:
                # Set outDir
                son.outDir = os.path.join(son.projDir, son.beamName)

                # Set colormap
                son.sonogram_colorMap = sonogram_colorMap

                # Determine what chunks to process
                chunkCnt = 0
                chunks = son._getChunkID()
                if son.wcp:
                    chunkCnt += len(chunks)
                if son.wcm:
                    chunkCnt += len(chunks)
                if son.wcr_src:
                    chunkCnt += len(chunks)
                if son.wco:
                    chunkCnt += len(chunks)

                # Load sonMetaDF
                son._loadSonMeta()

                for i in chunks:
                    son._exportTilesSpd(i, tileFile=imgType,
                                        spdCor=spdCor, mask_shdw=mask_shdw, maxCrop=maxCrop)

                if moving_window and not spdCor:

                    # Crop all images to most common range
                    son._loadSonMeta()
                    sDF = son.sonMetaDF

                    rangeCnt = np.unique(sDF['ping_cnt'], return_counts=True)
                    pingMaxi = np.argmax(rangeCnt[1])
                    pingMax = int(rangeCnt[0][pingMaxi])

                    depCnt = np.unique(sDF['dep_m'], return_counts=True)
                    depMaxi = np.argmax(depCnt[1])
                    depMax = int(depCnt[0][depMaxi]/sDF['pixM'][0])
                    depMax += 50

                    # Remove first chunk
                    chunks.sort()
                    chunks = chunks[1:]

                    # Get types of files exported
                    tileType = []
                    if son.wcp:
                        tileType.append('wcp')
                    if son.wcm:
                        tileType.append('wcm')
                    if son.wcr_src:
                        tileType.append('src')
                    if son.wco:
                        tileType.append('wco')

                    for i in chunks:
                        son._exportMovWin(
                            i, stride=window_stride, tileType=tileType, pingMax=pingMax, depMax=depMax)

                    # son._exportMovWin(chunks,
                    #                   stride=window_stride,
                    #                   tileType=tileType)

                    for t in tileType:
                        shutil.rmtree(os.path.join(son.outDir, t))

                son._pickleSon()

            # Tidy up
            son._cleanup()
            gc.collect()

        del son

    ##############################################
    # Let's pickle sonObj so we can reload later #
    ##############################################

    for son in sonObjs:
        son._pickleSon()
    gc.collect()

    if len(ss_chan_avail) == 0:
        return False
    else:
        return True
