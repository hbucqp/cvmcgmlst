#!/usr/bin/python3

# -*- coding:utf-8 -*-

import os
import sys
import argparse
import subprocess
import pandas as pd
from Bio import SeqIO
from .cgmlst_core import mlst


def args_parse():
    "Parse the input argument, use '-h' for help."
    parser = argparse.ArgumentParser(
        usage='cvmcgmlst -i <genome assemble directory> -o <output_directory> \n\nAuthor: Qingpo Cui(SZQ Lab, China Agricultural University)\n')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-i", help="<input_path>: the PATH to the directory of assembled genome files. Could not use with -f")
    group.add_argument(
        "-f", help="<input_file>: the PATH of assembled genome file. Could not use with -i")
    parser.add_argument('-db', help="<database_path>: path of cgMLST database")
    parser.add_argument("-o", help="<output_directory>: output PATH")
    parser.add_argument('-minid', default=95,
                        help="<minimum threshold of identity>, default=95")
    parser.add_argument('-mincov', default=90,
                        help="<minimum threshold of coverage>, default=90")
    parser.add_argument('-create_db', action='store_true',
                        help='<initialize the reference database>')
    # parser.add_argument('-scheme', help='<the cgmlst scheme>')
    parser.add_argument(
        '-t', default=8, help='<number of threads>: default=8')
    parser.add_argument('-v', '--version', action='version',
                        version='Version: ' + get_version("__init__.py"), help='Display version')
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args()


def read(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()


def get_version(rel_path: str) -> str:
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


def initialize_db(fasta_file):
    print("Creating cgmlst blast database...")
    mlst.makeblastdb(fasta_file)


def main():
    df_all = pd.DataFrame()
    args = args_parse()
    if args.create_db:
        if args.db:
            print('Initailizing reference database ...')
            initialize_db(args.db)
            print('Finishing reference database creation.')
        else:
            print('Please use -create_db and -db simultaneously!')

    # elif args.init:
    #     initialize_db()

    print('Start cgMLST analysis ...')
    # threads
    threads = args.t
    # print(threads)

    minid = args.minid
    mincov = args.mincov

    # check if the output directory exists
    if not os.path.exists(args.o):
        os.mkdir(args.o)
    output_path = os.path.abspath(args.o)
    # print(output_path)

    # get the database path
    database_path = os.path.abspath(args.db)

    files = []

    if args.i is not None:
        # get the input path
        files = os.listdir(os.path.abspath(args.i))
        input_path = os.path.abspath(args.i)
    else:
        files.append(os.path.abspath(args.f))
        input_path = os.path.dirname(os.path.abspath(args.f))

    if len(files) == 0:
        print('No fasta files was found, Please check the input path!')
    else:
        for file in files:
            file_base = str(os.path.basename(os.path.splitext(file)[0]))
            output_filename = file_base + '_tab.txt'
            # print(output_path)
            # print('xxx')
            # print(file_base)
            outfile = os.path.join(output_path, output_filename)
            # print(outfile)
            file_path = os.path.join(input_path, file)
            # print(file_path)
            if os.path.isfile(file_path):
                # print("TRUE")
                if mlst.is_fasta(file_path):
                    print(f'Processing {file}')
                    result = mlst(file_path, database_path, output_path,
                                threads, minid, mincov).biopython_blast()
                    # print(df)
                    if len(result) != 0:
                        df = pd.DataFrame.from_dict(result, orient='index')
                        df.index.name = 'Loci'
                        df.rename(columns={0: 'Allele_Num'}, inplace=True)
                        df_trans = df.T
                        df_trans.index = [file_base]

                        # df_out['FILE'] = file_base
                        # order = list(reversed(df.columns.to_list()))
                        # df = df[order]
                        # print(df)
                        df.to_csv(outfile, sep='\t', index=True)
                        print(
                            f"Finishing process {file}: writing results to " + str(outfile))
                    else:
                        print('Empty result')
                        df=pd.DataFrame(columns=['Allele_Num'])
                        print(df)
                        df.index.name = 'Loci'
                        df_trans = df.T
                        df_trans.index = [file_base]
                    df_all = pd.concat([df_all, df_trans])
            else:
                next

    # output final pivot dataframe to outpu_path
    summary_file = os.path.join(output_path, 'cgmlst_summary.csv')
    df_all.index.name = 'Strain'
    df_all.to_csv(summary_file, index=True)


if __name__ == '__main__':
    main()
