"""Library for running Bruker image ripping utility."""

import argparse
import logging
import os
import pathlib

import h5py
import tifffile

logger = logging.getLogger(__name__)

HDF5_KEY = '/data'  # Default key name in Suite2P.


class TiffToHdf5Error(Exception):
    """Error during conversion of TIFF stack to HDF5."""


def tiff_to_hdf(infile, outfile):
    """Convert a directory of tiff files ripped from Bruker into a single HDF5 file."""
    os.makedirs(outfile.parent, exist_ok=True)
    logger.info('Reading TIFF data')
    try:
        data = tifffile.imread(infile)
    except TypeError:  # Error generated when infile does not exist (why not FileNotFound?)
        raise TiffToHdf5Error('Error reading input file.  Make sure file exists and is readable:\n%s' % infile)
    logger.info('Read TIFF data with shape %s and type %s', data.shape, data.dtype)
    logger.info('Writing data to hdf5')
    with h5py.File(outfile, 'w') as h5file:
        h5file.create_dataset(HDF5_KEY, data=data)
    logger.info('Done')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(module)s:%(lineno)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    parser = argparse.ArgumentParser(description='Convert tiff directory into hdf5 format')
    parser.add_argument('--infile', type=pathlib.Path, required=True, help='First OME TIFF file in the stack.')
    parser.add_argument(
        '--outfile',
        type=pathlib.Path,
        required=True,
        help='Output directory in which to store hdf5 file and metadata json file (must end in .h5 or .hdf5).')
    args = parser.parse_args()

    if args.outfile.suffix not in {'.h5', '.hdf5'}:
        raise TiffToHdf5Error('HDF5 outfile suffix should be .h5 or .hdf5 for compatibility with Suite2p')

    tiff_to_hdf(args.infile, args.outfile)
