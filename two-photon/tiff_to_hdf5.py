"""Library for running Bruker image ripping utility."""

import argparse
import logging
import os
import pathlib

import h5py
import tifffile

logger = logging.getLogger(__name__)

HDF5_KEY = '/data'  # Default key name in Suite2P.

TIFF_RE = r'^.*_Cycle(?P<cycle>\d{5})_Ch(?P<channel>\d+)_(?P<num>\d{6}).ome.tif$'
TIFF_GLOB = '*_Cycle*_Ch{channel}_*.ome.tif'


class TiffToHdf5Error(Exception):
    """Error during conversion of TIFF stack to HDF5."""


def tiff_to_hdf(infile, outfile, delete_tiffs):
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
    logger.info('Done writing data')

    if delete_tiffs:
        logger.info('Deleting tiff files')
        channel = infile.match(TIFF_RE).group('channel')
        tiff_files = infile.parent.glob(TIFF_GLOB.format(channel=channel))
        logger.info('Found %d tiffs to delete with channel %s', len(tiff_files), channel)
        for tiff_file in tiff_files:
            tiff_file.unlink()
        logger.info('Done deleting tiff files')

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
    parser.add_argument('--delete_tiffs', type=bool, action='store_true', help='Remove all tiff files when complete.')
    args = parser.parse_args()

    inmatch = args.infile.match(TIFF_RE)
    if not inmatch:
        raise TiffToHdf5Error('--infile does not fit expected pattern: *_CycleXXXXX_ChY_ZZZZZZ.ome.tif')
    if inmatch.group('cycle') != '00001':
        raise TiffToHdf5Error('--infile should be cycle 00001')
    if inmatch.group('num') != '000001':
        raise TiffToHdf5Error('--infile should be frame number 000001')

    if args.outfile.suffix not in {'.h5', '.hdf5'}:
        raise TiffToHdf5Error('--outfile suffix should be .h5 or .hdf5 for compatibility with Suite2p')

    tiff_to_hdf(args.infile, args.outfile, args.delete_tiffs)
