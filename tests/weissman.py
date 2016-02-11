#!/usr/bin/env python
"""Compute the Weissman Score of a compression algorithm.

The Weissman Score is a fictional perfomance score for lossless data compression
algorithms devised by Tsachy Weissman and Vinith Misra at Stanford University
and used in the HBO comedy series *Silicon Valley*.

The Weissman score W is computed as:

:math:`W = \alpha \frac{r}{\overline{r}} \frac{log(\overline{T})}{log(T)}`

where :math`r` and :math`T` refer to the compression ratio and time-to-compress
of the target algorithm, :math`r` and :math`T` refer to same quantities for a
standard universal compressor (in this implementation gzip is used) and
:math`\alpha` is a scaling constant. 

Further information here:
http://online.wsj.com/news/articles/SB10001424052702303987004579479244213599118

Usage:
  python weissman.py -c <command> -i <input> -o <output> -r <repetitions> -a <alpha>
  python weissman.py (--help | -h)
  python weissman.py (--version | -v)

Options:
  -c <command>    --command <command>     Command to make target algorithm compress <input> file into <output>
  -i <input>      --input <input>         Path of the input (uncompressed) file
  -o <output>     --output <output>       Path to the output (compressed) file generated by <command>
  -a <alpha>      --alpha <alpha>         Scaling parameter of Weissman score
  -r <reps>       --repetitions <reps>    Number of times to repeat the experiment (mean values are used to compute the score)
  -h              --help                  Show help       
  -v              --version               Show version
"""
from __future__ import division

import os
import sys
import time
import gzip
import tempfile
import subprocess
from math import log

import argparse

__version__ = 0.1

def gzip_compr_test(fname, compresslevel=9):
    """Return compression ratio and time-to-compress using gzip
    
    Parameters
    ----------
    fname : string
        The path to the file to compress
    compresslevel : int, optional
        The compression level used
    
    Returns
    -------
    r : float
        The compression ratio
    T : float
        The time-to-compress
    """
    fname_compr = tempfile.mkstemp(suffix='.gz')[1]
    with open(fname, 'rb') as f_in:
        with gzip.open(fname_compr, 'wb', compresslevel=compresslevel) as f_out:
            t_start = time.time()
            f_out.writelines(f_in)
            T = time.time() - t_start
    r = os.path.getsize(fname)/os.path.getsize(fname_compr)
    os.remove(fname_compr)
    return r, T

def target_compr_test(command, fname_in, fname_out):
    """Return compression ratio and time-to-compress using a given compression 
    algorithm
    
    Parameters
    ----------
    command : string
        The command for executing the compression algorithm
    fname_in : string
        The path to the uncompressed file which will be compressed by the command
    fname_out : string
        The path to the compressed file generated by the command
    
    Returns
    -------
    r : float
        The compression ratio
    T : float
        The time-to-compress
    """
    t_start = time.time()
    retcode = subprocess.call(command.split(" "))
    T = time.time() - t_start
    r = os.path.getsize(fname_in)/os.path.getsize(fname_out)
    if retcode != 0:
        raise ValueError("The target algorithm returned with code %d, something went wrong"
                         % retcode)
    os.remove(fname_out)
    return r, T

def weissman(command, fname_in, fname_out, alpha, reps):
    """Compute the Weissman score of a compression algorithm using Gzip as
    baseline.
    
    Parameters
    ----------
    command : string
        The command for executing the compression algorithm
    fname_in : string
        The path to the uncompressed file which will be compressed by the command
    fname_out : string
        The path to the compressed file generated by the command
    alpha : float
        The scaling factor
    reps : int
        The number of times compression test is repeated
        
    Returns
    -------
    W : float
        The Weissman score
    """
    mean = lambda x: sum(x)/len(x)
    r, T = [mean(x)
            for x in zip(*[target_compr_test(command, fname_in, fname_out)
                           for _ in range(reps)])]
    r_b, T_b = [mean(x)
                for x in zip(*[gzip_compr_test(fname_in)
                               for _ in range(reps)])]
    return alpha * (r/r_b) * (log(T_b)/log(T))

def main():
    parser = argparse.ArgumentParser(description="Compute Weissman Score of a "
                                     "lossless compression algorithm")
    parser.add_argument("-v", "--version", action="version",
                        version="%s" % __version__)
    parser.add_argument("-c", "--command", dest="command",
                        help="Command to make test algorithm compress INPUT file into OUTPUT",
                        required=True)
    parser.add_argument("-i", "--input", dest="input",
                        help="the input (uncompressed) file",
                        required=True)
    parser.add_argument("-o", "--output", dest="output",
                        help="the output (compressed) file generated by COMMAND",
                        required=True)
    parser.add_argument("-a", "--alpha", dest="alpha", type=float,
                        help="the alpha coefficient of the Weissman score",
                        required=True)
    parser.add_argument("-r", "--repetitions", dest="reps", type=int,
                        help="the number of times to repeat the compression test",
                        required=True)
    args = parser.parse_args()
    if args.alpha <= 0:
        sys.exit("The ALPHA argument must be positive")
    if args.reps <= 0:
        sys.exit("The REPETITIONS argument must be positive")
    W = weissman(args.command, args.input, args.output, args.alpha, args.reps)
    print('Weissman score: %s' % str(W))

if __name__ == '__main__':
    sys.exit(main())