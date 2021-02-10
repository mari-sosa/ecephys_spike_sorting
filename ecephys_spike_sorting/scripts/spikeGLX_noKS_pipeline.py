import os
import shutil
import subprocess
import numpy as np

from helpers import SpikeGLX_utils
from helpers import log_from_json
from create_input_json import createInputJson

# script to run CatGT, KS2, postprocessing and TPrime on data collected using
# SpikeGLX. The construction of the paths assumes data was saved with
# "Folder per probe" selected (probes stored in separate folders) AND
# that CatGT is run with the -out_prb_fld option

# -------------------------------
# -------------------------------
# User input -- Edit this section
# -------------------------------
# -------------------------------
run_file_base = "20201226_C25R1_Day23_CenterRow180_TipRef_2"
# -----------
# Input data
# -----------
# Name for log file for this pipeline run. Log file will be saved in the
# output destination directory catGT_dest
logName = f'{run_file_base}_log.csv'

# Raw data directory = npx_directory
# run_specs = name, gate, trigger and probes to process
npx_directory = r'/opt/handeldata/rig43/DATA/' #this should be the parent directory for spikeglx, 
# not the specific recording # 20201002_MS2_Day4_Bank2_g0/20201002_MS2_Day4_Bank2_g0_imec0'

# Each run_spec is a list of 4 strings:
#   undecorated run name (no g/t specifier, the run field in CatGT)
#   gate index, as a string (e.g. '0')
#   triggers to process/concatenate, as a string e.g. '0,400', '0,0 for a single file
#           can replace first limit with 'start', last with 'end'; 'start,end'
#           will concatenate all trials in the probe folder
#   probes to process, as a string, e.g. '0', '0,3', '0:3'

# run_specs should be the undecorated recording name, until the gate id i.e '_g0'
run_specs = [										
						[run_file_base, '1', '0,0', '0']
]

# ------------------
# Output destination
# ------------------
# Set to an existing directory; all output will be written here.
# Output will be in the standard SpikeGLX directory structure:
# run_folder/probe_folder/*.bin
catGT_dest = os.path.join('/opt/handeldata/rig43/preprocessed/', run_file_base) #20201002_MS2_Day4_Bank2/'

# ------------
# CatGT params
# ------------
run_CatGT = True   # set to False to sort/process previously processed data.
# catGT streams to process, e.g. just '-ap' for ap band only, '-ap -ni' for
# ap plus ni aux inputs
catGT_stream_string = '-ap -ni -lf'

# CatGT command string includes all instructions for catGT operations
# Note 1: directory naming in this script requires -prb_fld and -out_prb_fld
# Note 2: this command line includes specification of edge extraction
# see CatGT readme for details
catGT_cmd_string = '-prb_fld -out_prb_fld -aphipass=300 -aplopass=6000 -lflopass=400 '\
        '-gbldmx -gfix=0.3,0.10,0.02 '\
        '-SY=0,384,6,500 '\
        '-XA=0,1,3,500 '\
<<<<<<< HEAD
        '-XA=1,1.9,2.3,10 '\
=======
        '-XA=1,2.5,2.49,0 '\
>>>>>>> cbc9b25 (run_file_base to var, XD word=2, no ms dur for camera pulse)
        '-XD=2,0,10 '\
        '-XD=2,1,10 '\
        '-XD=2,2,10 '\
        '-XD=2,3,10 '\
        '-XD=2,4,0 '\
        '-XD=2,5,0 '\
        '-XD=2,6,0 '\
        '-XD=2,7,0 '\
        '-XD=2,8,0 '\
        '-XD=2,9,0 '\
        '-XD=2,10,0 '\
        '-XD=2,11,0 '\
        '-XD=2,12,0 '\
        '-XD=2,13,0 '\
        '-XD=2,14,0 '\
        '-XD=2,15,0'


# M.S. ni aux inputs ----------
# gfix=0.3,0.10,0.02 -- artifact removal. |amp(mV)|,|slope(mV/sample)|,noise 
# XA=0,1,3,500 -- sync channel on nidaq: word 0, thresh 1 V(?), must stay above 3V, dur 500 ms
# XA=1,1,1.5,10 -- camera: word 1, thresh 1 V(?), must stay above 1.5V, dur 10  ms
# XD=0,0,10 -- Well 0 LED: word 0, bit 0, dur 100  ms (for MS2 day4, these are IR beam break)
# XD=0,1,10 -- Well 1 LED: word 0, bit 1, dur 100  ms
# XD=0,2,10 -- Well 2 LED: word 0, bit 2, dur 100  ms
# XD=0,3,10 -- Well 3 LED: word 0, bit 3, dur 100  ms
# XD=0,4,10 -- Well 0 IR detect: word 0, bit 4, dur 10  ms
# XD=0,5,10 -- Well 1 IR detect: word 0, bit 5, dur 10  ms
# XD=0,6,10 -- Well 2 IR detect: word 0, bit 6, dur 10  ms
# XD=0,7,10 -- Well 3 IR detect: word 0, bit 7, dur 10  ms
# XD=0,8,10 -- Well 0 IR beam break: word 0, bit 8, dur 10  ms (for MS2 day4, these are IR beam break)
# XD=0,9,10 -- Well 1 IR beam break: word 0, bit 9, dur 10  ms
# XD=0,10,10 -- Well 2 IR beam break: word 0, bit 10, dur 10  ms
# XD=0,11,10 -- Well 3 IR beam break: word 0, bit 11, dur 10  ms
# XD=0,12,10 -- Well 0 pump: word 0, bit 12, dur 100  ms
# XD=0,13,10 -- Well 1 pump: word 0, bit 13, dur 100  ms
# XD=0,14,10 -- Well 2 pump: word 0, bit 14, dur 100  ms
# XD=0,15,10 -- Well 3 pump: word 0, bit 15, dur 100  ms

# ------------------------------

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
toStream_sync_params = 'SY=0,384,6,500' # copy from the CatGT command line, no spaces
niStream_sync_params = 'XA=0,1,3,500'   # copy from the CatGT comman line, set to None if no Aux data, no spaces

# ---------------
# Modules List
# ---------------
# List of modules to run per probe; CatGT and TPrime are called once for each run.
# M.S. removed 'psth_events'
modules = [ ]

json_directory = os.path.join('/opt/handeldata/rig43/preprocessed', run_file_base) #r'/home/rig43/local_repos/ecephys_spike_sorting/ecephys_spike_sorting/json_files'

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

# delete any existing log with the current name
logFullPath = os.path.join(catGT_dest, logName)
try:
    os.remove(logFullPath)
except OSError:
    pass

# create the log file, write header
log_from_json.writeHeader(logFullPath)

for spec in run_specs:

    session_id = spec[0]

    # Run CatGT
    input_json = os.path.join(json_directory, session_id + '-input.json')
    output_json = os.path.join(json_directory, session_id + '-output.json')
    
    # Make list of probes from the probe string
    prb_list = SpikeGLX_utils.ParseProbeStr(spec[3])
    
    # build path to the first probe folder
    run_folder_name = spec[0] + '_g' + spec[1]
    prb0_fld_name = run_folder_name + '_imec' + prb_list[0]
    prb0_fld = os.path.join(npx_directory, run_folder_name, prb0_fld_name)
    first_trig, last_trig = SpikeGLX_utils.ParseTrigStr(spec[2], prb0_fld)
    trigger_str = repr(first_trig) + ',' + repr(last_trig)
    
    print('Creating json file for preprocessing')
    info = createInputJson(input_json, npx_directory=npx_directory, 
	                                   continuous_file = None,
                                       spikeGLX_data = 'True',
									   kilosort_output_directory=catGT_dest,
                                       catGT_run_name = session_id,
                                       gate_string = spec[1],
                                       trigger_string = trigger_str,
                                       probe_string = spec[3],
                                       catGT_stream_string = catGT_stream_string,
                                       catGT_cmd_string = catGT_cmd_string,
                                       extracted_data_directory = catGT_dest
                                       )

    # CatGT operates on whole runs with multiple probes, so gets called in just
    # once per run_spec
    if run_CatGT:
        command = "python -W ignore -m ecephys_spike_sorting.modules." + 'catGT_helper' + " --input_json " + input_json \
		          + " --output_json " + output_json
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
         
    # finsihed preprocessing. All other modules are are called once per probe

    for i, prb in enumerate(prb_list):
        #create json files specific to this probe
        session_id = spec[0] + '_imec' + prb
        input_json = os.path.join(json_directory, session_id + '-input.json')
        
        
        # location of the binary created by CatGT, using -out_prb_fld
        run_str = spec[0] + '_g' + spec[1]
        run_folder = 'catgt_' + run_str
        prb_folder = run_str + '_imec' + prb
        data_directory = os.path.join(catGT_dest, run_folder, prb_folder)
        fileName = run_str + '_tcat.imec' + prb + '.ap.bin'
        continuous_file = os.path.join(data_directory, fileName)
 
        outputName = 'imec' + prb + '_ks2'

        # kilosort_postprocessing and noise_templates moduules alter the files
        # that are input to phy. If using these modules, keep a copy of the
        # original phy output
        if ('kilosort_postprocessing' in modules) or('noise_templates' in modules):
            ks_make_copy = True
        else:
            ks_make_copy = False

        kilosort_output_dir = os.path.join(data_directory, outputName)

        print(data_directory)
        print(continuous_file)

        info = createInputJson(input_json, npx_directory=npx_directory, 
	                                   continuous_file = continuous_file,
                                       spikeGLX_data = True,
									   kilosort_output_directory=kilosort_output_dir,
                                       ks_make_copy = ks_make_copy,
                                       noise_template_use_rf = False,
                                       catGT_run_name = session_id,
                                       gate_string = spec[1],
                                       trigger_string = trigger_str,
                                       probe_string = spec[3],
                                       catGT_stream_string = catGT_stream_string,
                                       catGT_cmd_string = catGT_cmd_string,
                                       catGT_gfix_edits = gfix_edits[i],
                                       extracted_data_directory = catGT_dest,
                                       event_ex_param_str = event_ex_param_str
                                       )   

        # copy json file to data directory as record of the input parameters (and gfix edit rates)  
        shutil.copy(input_json, os.path.join(data_directory, session_id + '-input.json'))
        
        for module in modules:
            output_json = os.path.join(json_directory, session_id + '-' + module + '-output.json')  
            command = "python -W ignore -m ecephys_spike_sorting.modules." + module + " --input_json " + input_json \
		          + " --output_json " + output_json
            subprocess.check_call(command.split(' '))
            
        log_from_json.addEntry(modules, json_directory, session_id, logFullPath)
                   
    if runTPrime:
        # after loop over probes, run TPrime to create files of 
        # event times -- edges detected in auxialliary files and spike times 
        # from each probe -- all aligned to a reference stream.
    
        # create json files for calling TPrime
        session_id = spec[0] + '_TPrime'
        input_json = os.path.join(json_directory, session_id + '-input.json')
        output_json = os.path.join(json_directory, session_id + '-output.json')
        
        info = createInputJson(input_json, npx_directory=npx_directory, 
    	                                   continuous_file = continuous_file,
                                           spikeGLX_data = True,
    									   kilosort_output_directory=kilosort_output_dir,
                                           ks_make_copy = ks_make_copy,
                                           noise_template_use_rf = False,
                                           catGT_run_name = spec[0],
                                           gate_string = spec[1],
                                           trigger_string = trigger_str,
                                           probe_string = spec[3],
                                           catGT_stream_string = catGT_stream_string,
                                           catGT_cmd_string = catGT_cmd_string,
                                           catGT_gfix_edits = gfix_edits[i],
                                           extracted_data_directory = catGT_dest,
                                           event_ex_param_str = event_ex_param_str,
                                           sync_period = 1.0,
                                           toStream_sync_params = toStream_sync_params,
                                           niStream_sync_params = niStream_sync_params,
                                           toStream_path_3A = ' ',
                                           fromStream_list_3A = list()
                                           ) 
        
        command = "python -W ignore -m ecephys_spike_sorting.modules." + 'tPrime_helper' + " --input_json " + input_json \
    		          + " --output_json " + output_json
        subprocess.check_call(command.split(' '))  
    
