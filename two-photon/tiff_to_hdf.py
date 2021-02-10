"""Library for running Bruker image ripping utility."""

import argparse
import logging
import os
import pathlib

import h5py
import tifffile

logger = logging.getLogger(__name__)

HDF5_KEY = '/data'  # Default key name in Suite2P.


def tiff_to_hdf(infile, outfile):
    """Convert a directory of tiff files ripped from Bruker into a single HDF5 file."""
    os.makedirs(outfile.parent, exist_ok=True)
    data = tifffile.imread(infile)
    with h5py.File(outfile, 'w') as h5file:
        h5file.create_dataset(HDF5_KEY, data=data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(module)s:%(lineno)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    parser = argparse.ArgumentParser(description='Convert tiff directory into hdf5 format')
    parser.add_argument('--infile',
                        type=pathlib.Path,
                        required=True,
                        help='First OME TIFF file in the stack.')
    parser.add_argument('--outfile',
                        type=pathlib.Path,
                        required=True,
                        help='Output directory in which to store hdf5 file and metadata json file.')

    args = parser.parse_args()
    tiff_to_hdf(args.infile, args.outfile)
