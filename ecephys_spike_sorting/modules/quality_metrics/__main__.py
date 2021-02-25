from argschema import ArgSchemaParser
import os
import logging
import time


import numpy as np
import pandas as pd

from ...common.utils import load_kilosort_data
from ...common.epoch import get_epochs_from_nwb_file

from .metrics import calculate_metrics


def calculate_quality_metrics(args):

    print('ecephys spike sorting: quality metrics module')

    start = time.time()
    
    include_pcs = args['quality_metrics_params']['include_pcs']

    print("Loading data...")

    try:
        if include_pcs:
            spike_times, spike_clusters, spike_templates, amplitudes, templates, channel_map, \
            channel_pos, clusterIDs, cluster_quality, cluster_amplitude, pc_features, pc_feature_ind, template_features = \
                    load_kilosort_data(args['directories']['kilosort_output_directory'], \
                        args['ephys_params']['sample_rate'], \
                        use_master_clock = False,
                        include_pcs = include_pcs)
        else:
            spike_times, spike_clusters, spike_templates, amplitudes, templates, channel_map, \
            channel_pos, clusterIDs, cluster_quality, cluster_amplitude = \
            load_kilosort_data(args['directories']['kilosort_output_directory'], \
                        args['ephys_params']['sample_rate'], \
                        use_master_clock = False,
                        include_pcs = include_pcs)
            pc_features = []
            pc_feature_ind = []
            

        metrics = calculate_metrics(spike_times, spike_clusters, amplitudes, channel_map, channel_pos, templates, pc_features, pc_feature_ind, args['quality_metrics_params'])

    except FileNotFoundError:
        
        execution_time = time.time() - start

        print(" Files not available.")

        return {"execution_time" : execution_time,
            "quality_metrics_output_file" : None} 

    
    output_file = args['cluster_metrics']['cluster_metrics_file']

    if os.path.exists(args['waveform_metrics']['waveform_metrics_file']):
        metrics = metrics.merge(pd.read_csv(args['waveform_metrics']['waveform_metrics_file'], index_col=0),
                     on='cluster_id',
                     suffixes=('_quality_metrics','_waveform_metrics'))

    print("Saving data...")
   

    metrics.to_csv(output_file)

    execution_time = time.time() - start

    print('total time: ' + str(np.around(execution_time,2)) + ' seconds')
    print()
    
    return {"execution_time" : execution_time,
            "quality_metrics_output_file" : output_file} # output manifest


def main():

    from ._schemas import InputParameters, OutputParameters

    mod = ArgSchemaParser(schema_type=InputParameters,
                          output_schema_type=OutputParameters)

    output = calculate_quality_metrics(mod.args)

    output.update({"input_parameters": mod.args})
    if "output_json" in mod.args:
        mod.output(output, indent=2)
    else:
        print(mod.get_output_json(output))


if __name__ == "__main__":
    main()
