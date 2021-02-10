"""Library for running Bruker image ripping utility."""

import argparse
import logging
import os
import pathlib

import metadata
import tiffdata

logger = logging.getLogger(__name__)

HDF5_KEY = '/data'  # Default key name in Suite2P.


def tiff_to_hdf(inprefix, channel, outdir):
    """Convert a directory of tiff files ripped from Bruker into a single HDF5 file."""
    os.makedirs(outdir, exist_ok=True)
    mdata = metadata.read(inprefix, outdir)
    data = tiffdata.read(inprefix, mdata['size'], mdata['layout'], channel)
    fname_data = outdir / 'data.hdf'
    data.to_hdf5(fname_data, HDF5_KEY)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(module)s:%(lineno)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    parser = argparse.ArgumentParser(description='Convert tiff directory into hdf5 format')
    parser.add_argument('--inprefix',
                        type=pathlib.Path,
                        required=True,
                        help='Prefix for the xml and tiff files used.')
    parser.add_argument('--outdir',
                        type=pathlib.Path,
                        required=True,
                        help='Output directory in which to store hdf5 file and metadata json file.')
    parser.add_argument('--channel', type=int, required=True, help='Microscrope channel containing the two-photon data')

    args = parser.parse_args()
    tiff_to_hdf(args.inprefix, args.channel, args.outdir)
