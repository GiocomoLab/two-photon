"""Library for determining artefact locations in a 2p dataset."""

import logging

import numpy as np
import pandas as pd
import pdb
import re
logger = logging.getLogger(__file__)


def get_frame_start(df_voltage, fname):
    #pdb.set_trace()
    im_trigger_name = 'ImageFrameTrigger'
    if not im_trigger_name in df_voltage:
        im_trigger_name = 'frame starts'
    frame_start_cat = df_voltage[im_trigger_name].apply(lambda x: 1 if x > 1 else 0)
    frame_start = frame_start_cat[frame_start_cat.diff() > 0.5].index
    frame_start.to_series().to_hdf(fname, 'frame_start', mode='a')
    logger.info('Stored calculated frame starts in %s, preview:\n%s', fname, frame_start[:5])
    return frame_start

def get_write_vrPulses(pulse_train,fname):
    vr_pulses = pulse_train>1 #turn it into boolean seres
    vr_timestamps = pulse_train[vr_pulses.diff()>0] #this works because diff on boolean series is xor operation, so both the upward and the downward will give True
    #### however, would not work for single pulse per frame, then do same as in get_frame_start ###
    vr_timestamps.to_hdf(fname,'vr_pulses',mode='a')


def get_bounds(df_voltage, frame_start, size, stim_channel_name, fname, buffer, shift, settle_time):
    """From a dataframe of experiment timings, return a dataframe of artefact locations in the data."""
    logger.info('Calculating artefact regions')

    shape = (size['frames'], size['z_planes'])
    n_frames = shape[0] * shape[1]
    frame_start = frame_start[0:n_frames]
    y_px = size['y_px']

    stim = df_voltage[stim_channel_name].apply(lambda x: 1 if x > 1 else 0)
    stim_start = stim[stim.diff() > 0.5].index + shift
    #stimstring = stim.astype(str).str.cat()
    
    #start=[m.start(0) for m in re.finditer('0011',stimstring)]
    #start = np.array(start)+2
    #stim_start = stim.iloc[start].index+shift
    #stim_stop = stim_start+shift+buffer+6.

    stim_stop = stim[stim.diff() < -0.5].index + shift + buffer
    #import pdb
    #pdb.set_trace()
    frame, z_plane, y_px_start, y_px_stop = get_start_stop(stim_start, stim_stop, frame_start, y_px, shape, settle_time)

    df = pd.DataFrame({'frame': frame, 'z_plane': z_plane, 'y_min': y_px_start, 'y_max': y_px_stop})
    df = df.set_index('frame')
    df.to_hdf(fname, 'data', mode='w')
    #import pdb
    #pdb.set_trace()
    df.to_csv(str(fname).replace('.h5','.csv')) #for matlab later on

    stim_start.to_series().to_hdf(fname, 'stim_start', mode='a')
    stim_stop.to_series().to_hdf(fname, 'stim_stop', mode='a')

    logger.info('Stored calculated artefact positions in %s, preview:\n%s', fname, df.head())
    return df


def get_start_stop(stim_start, stim_stop, frame_start, y_px, shape, settle_time):
    ix_start, y_off_start = get_loc(stim_start, frame_start, y_px, shape, settle_time)
    y_off_start = np.floor(y_off_start).astype(int)
    ix_stop, y_off_stop = get_loc(stim_stop, frame_start, y_px, shape, settle_time)
    y_off_stop = np.ceil(y_off_stop).astype(int)

    frame = []
    z_plane = []
    y_px_start = []
    y_px_stop = []
    for (ix_start_cyc, ix_start_z), (ix_stop_cyc, ix_stop_z), y_min, y_max in zip(ix_start, ix_stop, y_off_start,
                                                                                  y_off_stop):
        if (ix_start_cyc == ix_stop_cyc) and (ix_start_z == ix_stop_z):
            if y_min == y_max:  # If a single-frame stim begins+ends during stim, skip it
                continue
            frame.append(ix_start_cyc)
            z_plane.append(ix_start_z)
            y_px_start.append(y_min)
            y_px_stop.append(y_max)
        else:  # Stim spans >1 plane.
            frame.append(ix_start_cyc)
            z_plane.append(ix_start_z)
            y_px_start.append(y_min)
            y_px_stop.append(y_px)

            frame.append(ix_stop_cyc)
            z_plane.append(ix_stop_z)
            y_px_start.append(0)
            y_px_stop.append(y_max)
    return frame, z_plane, y_px_start, y_px_stop


def get_loc(times, frame_start, y_px, shape, settle_time):
    """Determine the location of event times within the data, given the frame start times."""
    v_idx = times < frame_start.max() #valid starts
    interp = np.interp(times[v_idx], frame_start, range(len(frame_start))) #convert time to fractional frame
    indices = interp.astype(int) #actual frame
    idx = np.transpose(np.unravel_index(indices, shape)) #convert to cycle and plane

    frame_times = (frame_start[1:] - frame_start[:-1])
    frame_times_stims = frame_times[indices]
    mft=np.full_like(frame_times,np.mean(frame_times)) #get rid of the jitter by the 5khz aux recording, assume frames are recorded regularly
    frame_times_stims = mft[indices]

    offset = (interp - indices) * frame_times_stims #in ms, how long after frame onset
    acquisition_times = frame_times_stims - settle_time
    #y_offset = y_px * offset / acquisition_times
    y_offset = y_px*offset/(0.995*acquisition_times)
    # If offset is greater than y_px, it has occurred during stim.  Cap at y_px.
    y_offset = np.minimum(y_px, y_offset)
    #import pdb
    #pdb.set_trace()
    return idx, y_offset
