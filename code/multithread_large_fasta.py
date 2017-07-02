#!/usr/bin/env python


#######################################
######DOCUMENT THIS FILE################
#######################################


from __future__ import division
from multiprocessing import Pool
import sys
import subprocess
import argparse
import os
import re
import shutil
from dirs_and_files import check_create_dir
from Bio import SeqIO
from Queue import Queue
from threading import Thread, Lock
import itertools
from Bio import SeqIO
import transcript_assembly as transcripts
import dirs_and_files as logistic
import protein_alignment

###############
###FUNCTIONS###
###############


count_sequences = 0
count_sequences_aat = 0
length_cluster = 0
length_cluster_aat = 0


def single_fasta(ref, wd):
    '''From a fasta file make single files with each sequence'''
    wd_split = wd + '/split/'
    logistic.check_create_dir(wd_split)
    fastaFile = open(ref, 'r')
    single_fasta_list = []
    for record in SeqIO.parse(fastaFile, "fasta"):
        fasta_name = wd_split + '/' + record.id + '.fasta'
        single_fasta_list.append(fasta_name)
        output_handle = open(fasta_name, "w")
        SeqIO.write(record, output_handle, "fasta")
        output_handle.close()
    return single_fasta_list


def parseAugustus(wd, single_fasta_list):
    '''From all the augustus output after the multithread generate a single gff file'''
    fileName = wd + '/augustus.gff'
    testGff = open(fileName, 'w')
    for root, dirs, files in os.walk(wd):
        for name in files:
            for ident in single_fasta_list:
                change_id = (ident.split('/')[-1]) + '.augustus.gff'
                if name == change_id:
                    wd_gff = os.path.join(root, name)
                    t_file = open(wd_gff, 'r')
                    for line in t_file:
                        testGff.write(line)
                    t_file.close()
    testGff.close()
    return fileName


def augustusParse(queue, species_name, wd):
    '''to join the assembly and the parsing process'''
    while True:
        try:
            ref = queue.get()
        except:
            break
        outputDir = transcripts.augustus_call(wd, ref, species_name)
        queue.task_done()
        global count_sequences
        count_sequences += 1
        global length_cluster
    return


def func_star(a_b):
    return augustusParse(*a_b)


def augustus_multi(ref, threads, species, single_fasta_list, wd):
    '''handles the assembly process and parsing in a multithreaded way'''
    augu_queue = Queue()
    counter = 1
    for record in single_fasta_list:
        augu_queue.put(record)
    global length_cluster
    length_cluster = str(augu_queue.qsize())

    for i in range(int(threads)):
        t = Thread(target=augustusParse, args=(augu_queue, species, wd))
        t.daemon = True
        t.start()
    augu_queue.join()
    parseAugustus(wd, single_fasta_list)


def aatParse(aat_queue, protein_evidence, wd):
    '''to join the assembly and the parsing process'''
    #count = 0
    while True:
        try:
            ref_aat = aat_queue.get()
        except:
            break
        outputDir_1 = protein_alignment.AAT(protein_evidence, ref_aat, wd)
        aat_queue.task_done()
        global count_sequences_aat
        count_sequences_aat += 1
        global length_cluster_aat

    return


def func_star(a_b):
    return aatParse(*a_b)


def aat_multi(ref, threads, protein_evidence, single_fasta_list, wd):
    '''handles the assembly process and parsing in a multithreaded way'''

    aat_queue = Queue()
    counter = 1
    for record_aat in single_fasta_list:
        aat_queue.put(record_aat)
    global length_cluster_aat
    length_cluster_aat = str(aat_queue.qsize())
    for a in range(int(threads)):
        b = Thread(target=aatParse, args=(aat_queue, protein_evidence, wd))
        b.daemon = True
        b.start()

    aat_queue.join()
    protein_alignment.parseAAT(wd)


def main():
    '''Main body of the function'''

    ref = os.path.abspath(sys.argv[1])
    threads = sys.argv[2]
    species = sys.argv[3]
    wd = os.path.abspath(sys.argv[4])

    augustus_multi(ref, threads, species, single_fasta_list, wd)

    print '\n\n\n###############\n###FINISHED###\n###############\n\n'


if __name__ == '__main__':
    main()
