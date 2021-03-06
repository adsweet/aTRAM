"""Base class for the various assembler programs."""

import sys
from shutil import which
import textwrap
import psutil
import lib.log as log
from lib.assemblers.abyss import AbyssAssembler
from lib.assemblers.spades import SpadesAssembler
from lib.assemblers.trinity import TrinityAssembler
from lib.assemblers.velvet import VelvetAssembler
from lib.assemblers.none import NoneAssembler


ASSEMBLERS = {
    'abyss': AbyssAssembler,
    'trinity': TrinityAssembler,
    'velvet': VelvetAssembler,
    'spades': SpadesAssembler,
    'none': NoneAssembler}


def factory(args, cxn):
    """Return the assembler based upon the configuration options."""
    name = args['assembler'].lower()
    assembler = ASSEMBLERS[name]
    return assembler(args, cxn)


def command_line_args(parser):
    """Add command-line arguments for the assemblers."""
    group = parser.add_argument_group('optional assembler arguments')

    group.add_argument('--no-long-reads', action='store_true',
                       help="""Do not use long reads during assembly.
                            (Abyss, Trinity, Velvet)""")

    group.add_argument('--kmer', type=int, default=64,
                       help="""k-mer size. The default is 64 for Abyss and
                            31 for Velvet. Note: the maximum kmer length
                            for Velvet is 31. (Abyss, Velvet)""")

    group.add_argument('--mpi', action='store_true',
                       help="""Use MPI for this assembler. The assembler
                            'must have been compiled to use MPI. (Abyss)""")

    group.add_argument('--bowtie2', action='store_true',
                       help="""Use bowtie2 during assembly. (Trinity)""")

    total_mem = psutil.virtual_memory().available >> 30
    max_mem = max(1.0, total_mem >> 1)
    group.add_argument('--max-memory',
                       default=max_mem, metavar='MEMORY', type=int,
                       help="""Maximum amount of memory to use in gigabytes.
                            We will use {} out of {} GB of free/unused memory.
                            (Trinity, Spades)""".format(max_mem, total_mem))

    group.add_argument('--exp-coverage', '--expected-coverage',
                       type=int, default=30,
                       help="""The expected coverage of the region.
                            The default is "30". (Velvet)""")

    group.add_argument('--ins-length', type=int, default=300,
                       help="""The size of the fragments used in the short-read
                            library. The default is "300". (Velvet)""")

    group.add_argument('--min-contig-length', type=int, default=100,
                       help="""The minimum contig length used by the assembler
                            itself. The default is "100". (Velvet)""")

    group.add_argument('--cov-cutoff', default='off',
                       help="""Read coverage cutoff value. Must be a positive
                            float value, or "auto", or "off".
                            The default is "off". (Spades)""")


def default_kmer(kmer, assembler):
    """Calculate default kmer argument."""
    if assembler == 'velvet' and kmer > 31:
        kmer = 31

    return kmer


def default_cov_cutoff(cov_cutoff):
    """Calculate default coverage cutoff argument."""
    if cov_cutoff in ['off', 'auto']:
        return cov_cutoff

    err = ('Read coverage cutoff value. Must be a positive '
           'float value, or "auto", or "off"')
    try:
        value = float(cov_cutoff)
    except ValueError:
        log.fatal(err)

    if value < 0:
        log.fatal(err)

    return cov_cutoff


def find_program(assembler_name, program, assembler_arg, option=True):
    """Make sure we can find the programs needed by the assembler."""
    if assembler_arg == assembler_name and option and not which(program):
        err = (textwrap.dedent("""
            We could not find the "{}" program. You either need to
            install it or you need to adjust the PATH environment
            variable with the "--path" option so that aTRAM can
            find it.""")).format(program)
        sys.exit(err)
