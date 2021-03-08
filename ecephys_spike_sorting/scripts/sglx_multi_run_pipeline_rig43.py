import os
import shutil
import subprocess
import numpy as np
import glob

from ecephys_spike_sorting.scripts.helpers import SpikeGLX_utils
from ecephys_spike_sorting.scripts.helpers import log_from_json
#from helpers import run_one_probe
from ecephys_spike_sorting.scripts.create_input_json import createInputJson


# script to run CatGT, KS2, postprocessing and TPrime on data collected using
# SpikeGLX. The construction of the paths assumes data was saved with
# "Folder per probe" selected (probes stored in separate folders) AND
# that CatGT is run with the -out_prb_fld option

# -------------------------------
# -------------------------------
# Start user input -- Edit this section
# -------------------------------
# -------------------------------
run_file_base = "20201224_C25R1_Day21_CenterRow180_TipRef"

# Raw data directory = npx_directory
# This should be the parent directory for spikeglx data, 
# not the specific recording directory
npx_directory = r'/opt/handeldata/rig43/DATA/'

# brain region specific params
# can add a new brain region by adding the key and value for each param
# can add new parameters -- any that are taken by create_input_json --
# by adding a new dictionary with entries for each region and setting the 
# according to the new dictionary in the loop to that created json files.
# refPerMS is the refractory period threshold for the ISI distribution, per brain region.
refPerMS_dict = {'default': 2.0, 'cortex': 2.0}

# threhold values appropriate for KS2, KS2.5
ksTh_dict = {'default':'[10,4]', 'cortex':'[9,4]'}
# threshold values appropriate for KS3.0
#ksTh_dict = {'default':'[9,9]', 'cortex':'[9,9]', 'medulla':'[9,9]', 'thalamus':'[9,9]'}


# ------------------
# Output destination
# ------------------
# Set to an existing directory; all output will be written here.
# Output will be in the standard SpikeGLX directory structure:
# run_folder/probe_folder/*.bin
catGT_dest = os.path.join('/opt/handeldata/rig43/preprocessed/', run_file_base) #20201002_MS2_Day4_Bank2/'

# -----------
# Input data
# -----------
# Name for log file for this pipeline run. Log file will be saved in the
# output destination directory catGT_dest
# If this file exists, new run data is appended to it
logName = f'{run_file_base}_log.csv'


# run_specs = name, gate, trigger and probes to process
# Each run_spec is a list of 5 strings:
#   1. undecorated run name (no g/t specifier, the run field in CatGT until the gate, i.e. '_g0')
#   2. gate index, as a string (e.g. '0', or 'start','last' e.g. '0,4')
#   3. triggers to process/concatenate, as a string e.g. '0,400', '0,0 for a single file
#           can replace first limit with 'start', last with 'end'; 'start,end'
#           will concatenate all trials in the probe folder
#   4. probes to process, as a string, e.g. '0', '0,3', '0:3'
#   5. brain regions, list of strings, one per probe, to set region specific params
#           these strings must match a key in the param dictionaries above.

run_specs = [										
		[run_file_base, '0,3', '0,0', '0',['cortex'] ]
            ]
#run_specs = [									
#	    	['SC024_092319_NP1.0_Midbrain', '0', '0,9', '0,1', ['cortex', 'medulla'] ]
#]

# ------------
# CatGT params
# ------------
run_CatGT = True   # set to False to sort/process previously processed data.


# CAR mode for CatGT. Must be equal to 'None', 'gbldmx', or 'loccar'
car_mode = 'gbldmx'
# inner and outer radii, in um for local comman average reference, if used
loccar_min = 40
loccar_max = 160

# CatGT commands for bandpass filtering, artifact correction, and zero filling
# Note 1: directory naming in this script requires -prb_fld and -out_prb_fld
# Note 2: this command line includes specification of edge extraction
# see CatGT readme for details
# these parameters will be used for all runs

# gfix=0,0.10,0.02 -- artifact removal; params: |thresh_amp(mV)|,|slope(mV/sample)|,noise
# -t_miss_ok option required to concatenate over missing g or t indices
# -zerofillmax=500 option required to fill gaps only up to 500ms of zeros,
# so kilsort doesn't crash
catGT_cmd_string = '-t_miss_ok -zerofillmax=500 -prb_fld -out_prb_fld -aphipass=300 -aplopass=6000 -lflopass=400 -gfix=0,0.10,0.02'
catGT_stream_string = '-ap -ni -lf'

ni_present = True
# ni_extract_string = '-XA=0,1,3,500 -XA=1,3,3,0 -XD=4,1,50 -XD=4,2,1.7 -XD=4,3,5'

# ----- NIDAQ INPUTS -----
# -- Each XA gets its own word, starting with 0. XA inputs must come first.
# -- XD inputs come next, on separate words from the XA inputs. 
# -- Each XD word contains up to 16 bits (0:15)
# -- rig43 inputs: --
# XA=0,1,3,500 -- sync channel on nidaq: word 0, thresh 1 V, must stay above 3V, dur 500 ms
# XA=1,1,1.5,0 -- camera: word 1, thresh 1 V, must stay above 1.5V, dur 10  ms
#                - check baseline and pulse height per animal/session
#                - duration must be within +/-20% of the actual pulse width; 0 ignores pulse width requirement
# XD=2,0,0 -- Well 0 LED: word 0, bit 0, dur 0  ms (for MS2 day4, these are IR beam break)
# XD=2,1,0 -- Well 1 LED: word 0, bit 1, dur 0  ms
# XD=2,2,0 -- Well 2 LED: word 0, bit 2, dur 0  ms
# XD=2,3,0 -- Well 3 LED: word 0, bit 3, dur 0  ms
# XD=2,4,0 -- Well 0 IR detect: word 0, bit 4, dur 0  ms
# XD=2,5,0 -- Well 1 IR detect: word 0, bit 5, dur 0  ms
# XD=2,6,0 -- Well 2 IR detect: word 0, bit 6, dur 0  ms
# XD=2,7,0 -- Well 3 IR detect: word 0, bit 7, dur 0  ms
# XD=2,8,0 -- Well 0 IR beam break: word 0, bit 8, dur 0  ms (for MS2 day4, theses are LED)
# XD=2,9,0 -- Well 1  IR beam break: word 0, bit 9, dur 0  ms
# XD=2,10,0 -- Well 2 IR beam break: word 0, bit 10, dur 0  ms
# XD=2,11,0 -- Well 3 IR beam break: word 0, bit 11, dur 0  ms
# XD=2,12,0 -- Well 0 pump: word 0, bit 12, dur 0  ms
# XD=2,13,0 -- Well 1 pump: word 0, bit 13, dur 0  ms
# XD=2,14,0 -- Well 2 pump: word 0, bit 14, dur 0  ms
# XD=2,15,0 -- Well 3 pump: word 0, bit 15, dur 0  ms

ni_extract_string = '-XA=0,1,3,500 '\
        '-XA=1,2.5,2.49,0 '\
        '-XD=2,0,0 '\
        '-XD=2,1,0 '\
        '-XD=2,2,0 '\
        '-XD=2,3,0 '\
        '-iXD=2,0,0 '\
        '-iXD=2,1,0 '\
        '-iXD=2,2,0 '\
        '-iXD=2,3,0 '\
        '-XD=2,4,0 '\
        '-XD=2,5,0 '\
        '-XD=2,6,0 '\
        '-XD=2,7,0 '\
        '-iXD=2,8,0 '\
        '-iXD=2,9,0 '\
        '-iXD=2,10,0 '\
        '-iXD=2,11,0 '\
        '-XD=2,12,0 '\
        '-XD=2,13,0 '\
        '-XD=2,14,0 '\
        '-XD=2,15,0'


# ----------------------
# KS2 or KS25 parameters
# ----------------------
# parameters that will be constant for all recordings
# Template ekmplate radius and whitening, which are specified in um, will be 
# translated into sites using the probe geometry.
ks_remDup = 0
ks_saveRez = 1
ks_copy_fproc = 0
ks_templateRadius_um = 163
ks_whiteningRadius_um = 163
ks_minfr_goodchannels = 0.05 #0.1


# ----------------------
# C_Waves snr radius, um
# ----------------------
c_Waves_snr_um = 160

# ----------------------
# psth_events parameters
# ----------------------
# extract param string for psth events -- copy the CatGT params used to extract
# events that should be exported with the phy output for PSTH plots
# If not using, remove psth_events from the list of modules
event_ex_param_str = 'XD=4,1,50'

# -----------------
# TPrime parameters
# -----------------
runTPrime = True   # set to False if not using TPrime
sync_period = 1.0   # true for SYNC wave generated by imec basestation
toStream_sync_params = 'SY=0,-1,6,500'  # copy from the CatGT command line, no spaces
niStream_sync_params = 'XA=0,1,3,500'   # copy from the CatGT comman line, set to None if no Aux data, no spaces

# ---------------
# Modules List
# ---------------
# List of modules to run per probe; CatGT and TPrime are called once for each run.
# M.S. removed 'psth_events'
modules = [
            'kilosort_helper',
            'kilosort_postprocessing',
            'noise_templates',
            'mean_waveforms',
            'quality_metrics'
			]

json_directory = os.path.join('/opt/handeldata/rig43/preprocessed', run_file_base) #20201002_MS2_Day4_Bank2' 

# -----------------------
# -----------------------
# End of user input
# -----------------------
# -----------------------

# delete the existing CatGT.log
try:
    os.remove('CatGT.log')
except OSError:
    pass

# delete existing Tprime.log
try:
    os.remove('Tprime.log')
except OSError:
    pass

# delete existing C_waves.log
try:
    os.remove('C_Waves.log')
except OSError:
    pass

# check for existent of catGT dest, mkdir if doesn't exist
if not os.path.isdir(catGT_dest):
    os.mkdir(catGT_dest)


# check for existence of log file, create if not there
logFullPath = os.path.join(catGT_dest, logName)
if not os.path.isfile(logFullPath):
    # create the log file, write header
    log_from_json.writeHeader(logFullPath)
    
    


for spec in run_specs:

    session_id = spec[0]

    
    # Make list of probes from the probe string
    prb_list = SpikeGLX_utils.ParseProbeStr(spec[3])
    
    # build path to the first probe folder; look into that folder
    # to determine the range of trials if the user specified t limits as
    # start and end
    run_folder_name = spec[0] + '_g' + spec[1]
    prb0_fld_name = run_folder_name + '_imec' + prb_list[0]
    prb0_fld = os.path.join(npx_directory, run_folder_name, prb0_fld_name)
    first_trig, last_trig = SpikeGLX_utils.ParseTrigStr(spec[2], prb_list[0], spec[1], prb0_fld)
    trigger_str = repr(first_trig) + ',' + repr(last_trig)
    
    # get list of g-indices to concatenate from data directory
    first_gate = spec[1][0]
    g_range = '[' + spec[1][0] + '-' + spec[1][-1] + ']'
    g_tocat = sorted(glob.glob(os.path.join(npx_directory,(run_file_base + '_g' + g_range))))
    glist = ''.join((x[-1]+'-') for x in g_tocat)[:-1] # g inds separated by dashes, minus the last dash

    print('Concatenating g indices ' + glist)
    
    # loop over all probes to build json files of input parameters
    # initalize lists for input and output json files
    catGT_input_json = []
    catGT_output_json = []
    module_input_json = []
    module_output_json = []
    session_id = []
    catgt_output_dir = []
    data_directory = []
    
    # first loop over probes creates json files containing parameters for
    # both preprocessing (CatGt) and sorting + postprocessing
    
    for i, prb in enumerate(prb_list):
            
        #create CatGT command for this probe
        print('Creating json file for CatGT on probe: ' + prb)
        catGT_input_json.append(os.path.join(json_directory, spec[0] + '_g' + glist + '_prb' + prb + '_CatGT' + '-input.json'))
        catGT_output_json.append(os.path.join(json_directory, spec[0] + '_g' + glist + '_prb' + prb + '_CatGT' + '-output.json'))
        
        # build extract string for SYNC channel for this probe
        sync_extract = '-SY=' + prb +',-1,6,500'
        
        # if this is the first probe proceessed, process the ni stream with it
        if i == 0 and ni_present:
            catGT_stream_string = '-ap -ni -lf'
            extract_string = sync_extract + ' ' + ni_extract_string
        else:
            catGT_stream_string = '-ap -lf'
            extract_string = sync_extract
        
        # build name of first trial/gate to be concatenated/processed;
        # allows reading of the metadata
        print('first gate ' + spec[1][0])
        print('gate string ' + spec[1])
        run_str = spec[0] + '_g' + spec[1][0] 
        run_folder = run_str
        prb_folder = run_str + '_imec' + prb
        input_data_directory = os.path.join(npx_directory, run_folder, prb_folder)
        fileName = run_str + '_t' + repr(first_trig) + '.imec' + prb + '.ap.bin'
        continuous_file = os.path.join(input_data_directory, fileName)
        metaName = run_str + '_t' + repr(first_trig) + '.imec' + prb + '.ap.meta'
        input_meta_fullpath = os.path.join(input_data_directory, metaName)
        
        # ----- RUN CatGT -----
        info = createInputJson(catGT_input_json[i], npx_directory=npx_directory, 
                                       continuous_file = continuous_file,
                                       kilosort_output_directory=catGT_dest,
                                       spikeGLX_data = True,
                                       input_meta_path = input_meta_fullpath,
                                       catGT_run_name = spec[0],
                                       gate_string = spec[1],
                                       gate_list_string = glist,
                                       trigger_string = trigger_str,
                                       probe_string = prb,
                                       catGT_stream_string = catGT_stream_string,
                                       catGT_car_mode = car_mode,
                                       catGT_loccar_min_um = loccar_min,
                                       catGT_loccar_max_um = loccar_max,
                                       catGT_cmd_string = catGT_cmd_string + ' ' + extract_string,
                                       extracted_data_directory = catGT_dest
                                       )      
        
        
        if run_CatGT:
            command = "python -W ignore -m ecephys_spike_sorting.modules." + 'catGT_helper' + " --input_json " + catGT_input_json[i] \
            	          + " --output_json " + catGT_output_json[i]
            subprocess.check_call(command.split(' '))           

            # parse the CatGT log and write results to command line
            print(f"probe_list {prb_list}")
            logPath = os.getcwd()
            gfix_edits = SpikeGLX_utils.ParseCatGTLog( logPath, spec[0], spec[1], prb_list )
        
            for i in range(0,len(prb_list)):
                edit_string = '{:.3f}'.format(gfix_edits[i])
                print('Probe ' + prb_list[i] + '; gfix edits/sec: ' + repr(gfix_edits[i]))
        else:
            # fill in dummy gfix_edits for running without preprocessing
            gfix_edits = np.zeros(len(prb_list), dtype='float64' )
        
        #create json files for the other modules
        session_id.append(spec[0] + '_g' + glist + '_imec' + prb)
        
        module_input_json.append(os.path.join(json_directory, session_id[i] + '-input.json'))
        
        
        # location of the binary created by CatGT, using -out_prb_fld
        # use glist for run string here: included g indices separated by dashes 
        run_str = spec[0] + '_g' + glist
        run_folder = 'catgt_' + run_str
        prb_folder = run_str + '_imec' + prb
        catgt_output_dir = os.path.join(catGT_dest, run_folder)
        data_directory.append(os.path.join(catGT_dest, run_folder, prb_folder))
        fileName = run_str + '_tcat.imec' + prb + '.ap.bin'
        continuous_file = os.path.join(data_directory[i], fileName)
 
        outputName = 'imec' + prb + '_ks2'
    
        # recursively rename files in the catgt output dir to match the gate list,
        #      if more than 1 gate was concatenated
        # first get files in the renamed directory matching the first g index
        if len(glist)>len(first_gate):
            f_to_rename = glob.glob((catgt_output_dir + '/**/*_g' + first_gate + '_*'),recursive=True)
            print('renaming catgt output...')
            for f in f_to_rename: 
                splt_f = f.rsplit(('_g' + first_gate), 1)
                new_f = ('_g' + glist).join(splt_f)
                #new_f = f.replace(('_g' + first_gate),('_g' + glist))
                if os.path.isdir(f):
                    mv_cmd = "mv " + f + " " + new_f
                    subprocess.call(mv_cmd,shell=True)
                    subf_to_rename =  glob.glob((new_f + '/**/*_g' + first_gate + '_*'),recursive=True)
                    for sf in subf_to_rename:
                        splt_f = sf.rsplit(('_g' + first_gate), 1)
                        new_f = ('_g' + glist).join(splt_f)
                        os.rename(sf,new_f)
                else:
                    os.rename(f,new_f)
                print(f"renamed {len(f_to_rename)} files or directries in catgt output dir.")

        # kilosort_postprocessing and noise_templates moduules alter the files
        # that are input to phy. If using these modules, keep a copy of the
        # original phy output
        if ('kilosort_postprocessing' in modules) or('noise_templates' in modules):
            ks_make_copy = True
        else:
            ks_make_copy = False

        kilosort_output_dir = os.path.join(data_directory[i], outputName)

        # get region specific parameters
        ks_Th = ksTh_dict.get(spec[4][i])
        refPerMS = refPerMS_dict.get(spec[4][i])
        print( 'ks_Th: ' + repr(ks_Th) + ' ,refPerMS: ' + repr(refPerMS))

        info = createInputJson(module_input_json[i], npx_directory=npx_directory, 
	                               continuous_file = continuous_file,
                                       spikeGLX_data = True,
                                       input_meta_path = input_meta_fullpath,
				       kilosort_output_directory=kilosort_output_dir,
                                       ks_make_copy = ks_make_copy,
                                       noise_template_use_rf = False,
                                       catGT_run_name = session_id[i],
                                       gate_string = spec[1],
                                       gate_list_string = glist,
                                       probe_string = spec[3],  
                                       ks_remDup = ks_remDup,                   
                                       ks_finalSplits = 1,
                                       ks_labelGood = 1,
                                       ks_saveRez = ks_saveRez,
                                       ks_copy_fproc = ks_copy_fproc,
                                       ks_minfr_goodchannels = ks_minfr_goodchannels,                  
                                       ks_whiteningRadius_um = ks_whiteningRadius_um,
                                       ks_Th = ks_Th,
                                       ks_CSBseed = 1,
                                       ks_LTseed = 1,
                                       ks_templateRadius_um = ks_templateRadius_um,
                                       extracted_data_directory = catGT_dest,
                                       event_ex_param_str = event_ex_param_str,
                                       c_Waves_snr_um = c_Waves_snr_um,                               
                                       qm_isi_thresh = refPerMS/1000
                                       )   

        # Run each module --- KS is run here ---
        for module in modules:
            module_output_json = os.path.join(json_directory, session_id[i] + '-' + module + '-output.json')  
            command = "python -W ignore -m ecephys_spike_sorting.modules." + module + " --input_json " + module_input_json[i] \
		          + " --output_json " + module_output_json
            subprocess.check_call(command.split(' '))
        
        # copy json file to data directory as record of the input parameters 
        log_from_json.addEntry(modules, json_directory, session_id[i], logFullPath)
        
    # loop over probes for processing.    
   # for i, prb in enumerate(prb_list):  
   #     
   #     run_one_probe.runOne( session_id[i],
   #              json_directory,
   #              data_directory[i],
   #              run_CatGT,
   #              catGT_input_json[i],
   #              catGT_output_json[i],
   #              modules,
   #              module_input_json[i],
   #              logFullPath )
                 
    # ----- RUN TPrime -----

    if runTPrime:
        # after loop over probes, run TPrime to create files of 
        # event times -- edges detected in auxialliary files and spike times 
        # from each probe -- all aligned to a reference stream.
    
        # create json files for calling TPrime
        session_id = spec[0] #+ '_TPrime'
        input_json = os.path.join(json_directory, spec[0] + '_g' + glist + '_prb' + prb + '_TPrime' + '-input.json') 
        output_json = os.path.join(json_directory, spec[0] + '_g' + glist + '_prb' + prb + '_TPrime' + '-input.json')
        
        # build list of sync extractions to send to TPrime
        im_ex_list = ''
        for i, prb in enumerate(prb_list):
            sync_extract = '-SY=' + prb +',-1,6,500'
            im_ex_list = im_ex_list + ' ' + sync_extract
            
        print('im_ex_list: ' + im_ex_list)     
        
        info = createInputJson(input_json, npx_directory=npx_directory, 
    	                                   continuous_file = continuous_file,
                                           spikeGLX_data = True,
                                           input_meta_path = input_meta_fullpath,
                                           catGT_run_name = session_id,
                                            gate_string = spec[1],
                                            gate_list_string = glist,
                                            probe_string = spec[3],  
    					   kilosort_output_directory=kilosort_output_dir,
                                           extracted_data_directory = catGT_dest,
                                           tPrime_im_ex_list = im_ex_list,
                                           tPrime_ni_ex_list = ni_extract_string,
                                           event_ex_param_str = event_ex_param_str,
                                           sync_period = 1.0,
                                           toStream_sync_params = toStream_sync_params,
                                           niStream_sync_params = niStream_sync_params,
                                           tPrime_3A = False,
                                           toStream_path_3A = ' ',
                                           fromStream_list_3A = list()
                                           ) 
        
        command = "python -W ignore -m ecephys_spike_sorting.modules." + 'tPrime_helper' + " --input_json " + input_json \
    		          + " --output_json " + output_json
        subprocess.check_call(command.split(' '))  
    

