# ecephys_spike_sorting pipeline: rig43 edition

Pre-processing pipeline for Chronic Neuropixels data acquired with [SpikeGLX](https://billkarsh.github.io/SpikeGLX/), from imec/nidaq extraction through Kilosort spike sorting and cluster labeling.

Original [ecephys repo by Jennifer Colonell](https://github.com/jenniferColonell/ecephys_spike_sorting) is upstream of our fork, set for fetching only.

### Elements of the pipeline
1. [CatGT](https://billkarsh.github.io/SpikeGLX/#catgt) v1.6 for Linux:
    * Bandpass filter ap (action potential) and lf (local field potential) .bin files
    * Common-average reference and remove noise artifacts from ap data
    * Concatenate mutiple SpikeGLX recording files:
        * by g-index ("gate"): when you press `Disable` and `Enable` in SpikeGLX, used for separating behavioral sessions within a day
        * by t-index ("trigger"): trial times initiated in spikeGLX, currently unused
        * across different file names: if you had to stop and start a new acquisition, resetting the run clock
    * Extract TTL pulse edges (rising or falling) from NIDAQ analog and digital inputs
        * identifies behavioral timestamps so they can be synced to the neural data
2. [Kilosort2](https://github.com/GiocomoLab/Kilosort2)
    * Run via Matlab2019a, Cuda 10.0 on Linux
3. [Kilosort post-processing](https://github.com/jenniferColonell/ecephys_spike_sorting/tree/master/ecephys_spike_sorting/modules/kilosort_postprocessing)
    * Remove duplicate spikes detected by kilosort
4. [Noise templates](https://github.com/jenniferColonell/ecephys_spike_sorting/tree/master/ecephys_spike_sorting/modules/noise_templates)
    * Classify clusters as noise based on a noise template, updates KS cluster labels in cluster_group.tsv
6. [Mean waveforms](https://github.com/jenniferColonell/ecephys_spike_sorting/tree/master/ecephys_spike_sorting/modules/mean_waveforms)
    * Calculate mean waveforms and waveform metrics of each cluster, using either:
        * [C_waves](https://billkarsh.github.io/SpikeGLX/#post-processing-tools): v1.8 for Linux
        * mean waveforms python module included in ecephys
7. [Quality metrics](https://github.com/jenniferColonell/ecephys_spike_sorting/tree/master/ecephys_spike_sorting/modules/quality_metrics)
    * Calculate cluster quality metrics and update KS cluster labels accordingly in cluster_group.tsv
8. [TPrime](https://billkarsh.github.io/SpikeGLX/#tprime) v1.5 for Linux:
    * Adjust NIDAQ pulse timestamps to match imec clock (spike time stamps) by adjusting for differences in sampling rates.

All are run via python modules, but CatGT, C_waves, and TPrime are C executables passed to the command line.


## Installation of rig43 ecephys

Pre-requisites:
* Install [Kilosort2 and Matlab2019a for Linux](https://github.com/GiocomoLab/labWiki/wiki/Kilosort2-Installation-for-Linux)
    * TO DO: update these instructions for non-CMGM Matlab
* Download and install [CatGT, C_Waves, and TPrime](https://billkarsh.github.io/SpikeGLX/#catgt)
    * __For each of these__:
        * Extract the downloaded zip file (to your home directory is fine).
        * Then install:
        ```
        $ cd ~/CatGT-linux
        $ chmod +x install.sh
        $ ./install.sh
        ```
        
clone the rig43 ecephys fork
```
$ git clone https://github.com/mari-sosa/ecephys_spike_sorting
```
checkout the rig43 active branch
```
$ git checkout rig43_catgt1.6
```

If this is the first time setting up ecephys, install the Matlab engine for python:
1. activate the ecephys virtual environment
2. cd to matlabroot directory
3. change permissions of build directory to writeable
4. run setup.py - this will install the matlab engine in your virtual env. Note that running setup.py with “sudo” won’t install in the virtual env!
```
$ cd ~/local_repos/ecephys_spike_sorting
$ pipenv shell
$ cd /usr/local/MATLAB/R2019a/extern/engines/python
$ sudo chmod -R 777 build/
$ python setup.py install
```

[Check out the original ecephys installation instructions.](https://github.com/jenniferColonell/ecephys_spike_sorting)


## Running ecephys

cd to ecephys top-level directory
```
$ cd ~/local_repos/ecephys_spike_sorting
```

activate virtual environment -- ecephys uses pipenv (`pip install --user pipenv` if needed)
```
$ pipenv shell
```


pip install the setup.py file to autoreload module changes
```
$ pip install -e .
```

### Option 1: Use the pipeline script 
Edit pipeline script of choice with the parameters to run. This is not preferred because it involves hard-coding run names and such, but it's fast and easy.
The working rig43 pipeline script as of March 2021 is `sglx_multi_run_pipeline_rig43.py`
```
$ cd ~/local_repos/ecephys_spike_sorting/ecephys_spike_sorting/scripts
```

Edit the run_specs variable using your favorite text editor.  \
Then run the pipeline:
```
$ python sglx_multi_run_pipeline_rig43.py
```

### Option 2: Use the wrapper -- COMING SOON.




