If this is the first time setting up ecephys, install the Matlab engine for python:
Installing Matlab engine for python:
1. activate the ecephys virtual environment
2. cd to matlabroot directory
3. change permissions of build directory to writeable
4. run the setup.py - this will install the matlab engine in your virtual env. Note that “sudo” doesn’t install in the virtual env!
```
cd ~/local_repos/ecephys_spike_sorting
pipenv shell
cd /usr/local/MATLAB/R2019a/extern/engines/python
sudo chmod -R 777 build/
python setup.py install
```


cd to ecephys parent directory
```
cd ~/local_repos/ecephys_spike_sorting
```

activate virtual environment. ecephys uses pipenv
```
pipenv shell
```

pip install the setup.py file to autoreload module changes
```
pip install -e .
```

cd to pipeline script of choice
```
cd ecephys_spike_sorting/scripts
```



