import time, argparse,re,os
from virus_filter import flu_filter
from virus_clean import virus_clean
from tree_refine import tree_refine
from tree_titer import HI_tree
from fitness_model import fitness_model
from process import process
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Align import MultipleSeqAlignment
import numpy as np
from itertools import izip

epitope_mask = np.fromstring("0000000000000000000000000000000000000000000011111011011001010011000100000001001011110011100110101000001100000100000001000110101011111101011010111110001010011111000101011011111111010010001111101110111001010001110011111111000000111110000000101010101110000000000011100100000001011011100000000000001001011000110111111000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", dtype='S1')
	
virus_config = {
	# data source and sequence parsing/cleaning/processing
	'virus':'H3N2',
	'alignment_file':'data/gisaid_epiflu_sequence.fasta',
	'fasta_fields':{0:'strain', 1:'accession', 3:'passage', 5:'date' },
	'outgroup':'A/Beijing/32/1992',
	'force_include':'source-data/HI_strains.txt',
	'force_include_all':True,
	'max_global':True,   # sample as evenly as possible from different geographic regions 
	'cds':[48,None], # define the HA1 start i n 0 numbering
	'n_iqd':3,     # standard deviations from clock

	# frequency estimation parameters
	'aggregate_regions': [  ("global", None), ("NA", ["NorthAmerica"]), ("EU", ["Europe"]), 
							("AS", ["China", "SoutheastAsia", "JapanKorea"]), ("OC", ["Oceania"]) ],
	'frequency_stiffness':10.0,
	'time_interval':(2005.0, 2015.1),
	'pivots_per_year':12.0,
	'min_freq':0.01,
	# define relevant clades in canonical HA1 numbering (+1)
	'clade_designations': { "3c3.a":[(128,'A'), (142,'G'), (159,'S')],
						   "3c3":  [(128,'A'), (142,'G'), (159,'F')],
						   "3c2.a":[(144,'S'), (159,'Y'), (225,'D'), (311,'H'),(489,'N')],
						   "3c2":  [(144,'N'), (159,'F'),(225,'N'), (489,'N')]
							},
	'verbose':2, 
	'tol':1e-4, #tolerance for frequency optimization
	'pc':1e-3, #pseudocount for frequencies 
	'extra_pivots': 6,  # number of pivot point for or after the last observations of a mutations
	'inertia':0.7,		# fraction of frequency change carry over in the stiffness term
}


class H3N2_filter(flu_filter):
	def __init__(self,min_length = 987, **kwargs):
		'''
		parameters
		min_length  -- minimal length for a sequence to be acceptable
		'''
		flu_filter.__init__(self, **kwargs)
		self.min_length = min_length
		self.vaccine_strains =[
				{ 
					"strain": "A/Wisconsin/67/2005",
					"db": "IRD",
					"accession": "CY163984",
					"date": "2005-08-31",
					"seq": "ATGAAGACTATCATTGCTTTGAGCTACATTCTATGTCTGGTTTTCGCTCAAAAACTTCCCGGAAATGACAACAGCACGGCAACGCTGTGCCTTGGGCACCATGCAGTACCAAACGGAACGATAGTGAAAACAATCACGAATGACCAAATTGAAGTTACTAATGCTACTGAGCTGGTTCAGAGTTCCTCAACAGGTGGAATATGCGACAGTCCTCATCAGATCCTTGATGGAGAAAACTGCACACTAATAGATGCTCTATTGGGAGACCCTCAGTGTGATGGCTTCCAAAATAAGAAATGGGACCTTTTTGTTGAACGCAGCAAAGCCTACAGCAACTGTTACCCTTATGATGTGCCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCCGGCACACTGGAGTTTAACGATGAAAGCTTCAATTGGACTGGAGTCACTCAAAATGGAACAAGCTCTTCTTGCAAAAGGAGATCTAATAACAGTTTCTTTAGTAGATTGAATTGGTTGACCCACTTAAAATTCAAATACCCAGCATTGAACGTGACTATGCCAAACAATGAAAAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGGTTACGGACAATGACCAAATCTTCCTGTATGCTCAAGCATCAGGAAGAATCACAGTCTCTACCAAAAGAAGCCAACAAACTGTAATCCCGAATATCGGATCTAGACCCAGAATAAGGAATATCCCCAGCAGAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCTCCTAGGGGTTACTTCAAAATACGAAGTGGGAAAAGCTCAATAATGAGATCAGATGCACCCATTGGCAAATGCAATTCTGAATGCATCACTCCAAATGGAAGCATTCCCAATGACAAACCATTTCAAAATGTAAACAGGATCACATATGGGGCCTGTCCCAGATATGTTAAGCAAAACACTCTGAAATTGGCAACAGGGATGCGAAATGTACCAGAGAAACAAACTAGAGGCATATTTGGCGCAATCGCGGGTTTCATAGAAAATGGTTGGGAGGGAATGGTGGATGGTTGGTACGGTTTCAGGCATCAAAATTCTGAGGGAATAGGACAAGCAGCAGATCTCAAAAGCACTCAAGCAGCAATCAATCAAATCAATGGGAAGCTGAATAGGTTGATCGGGAAAACCAACGAGAAATTCCATCAGATTGAAAAAGAATTCTCAGAAGTAGAAGGGAGAATTCAGGACCTCGAGAAATATGTTGAGGACACTAAAATAGATCTCTGGTCATACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATCTAACTGACTCAGAAATGAACAAACTGTTTGAAAGAACAAAGAAGCAACTGAGGGAAAATGCTGAGGATATGGGCAATGGTTGTTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCATGATGTATACAGAGATGAAGCATTAAACAACCGGTTCCAGATCAAAGGCGTTGAGCTGAAGTCAGGATACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGTTTTTTGCTTTGTGTTGCTTTGTTGGGGTTCATCATGTGGGCCTGCCAAAAAGGCAACATTAGGTGCAACATTTGCATTTGA"
				},	{
					"strain": "A/Brisbane/10/2007",
					"db": "IRD",
					"accession": "CY113005",
					"date": "2007-02-06",
					"seq": "ATGAAGACTATCATTGCTTTGAGCTACATTCTATGTCTGGTTTTCACTCAAAAACTTCCCGGAAATGACAACAGCACGGCAACGCTGTGCCTTGGGCACCATGCAGTACCAAACGGAACGATAGTGAAAACAATCACGAATGACCAAATTGAAGTTACTAATGCTACTGAGCTGGTTCAGAGTTCCTCAACAGGTGAAATATGCGACAGTCCTCATCAGATCCTTGATGGAGAAAACTGCACACTAATAGATGCTCTATTGGGAGACCCTCAGTGTGATGGCTTCCAAAATAAGAAATGGGACCTTTTTGTTGAACGCAGCAAAGCCTACAGCAACTGTTACCCTTATGATGTGCCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCCGGCACACTGGAGTTTAACAATGAAAGCTTCAATTGGACTGGAGTCACTCAAAACGGAACAAGCTCTGCTTGCATAAGGAGATCTAATAACAGTTTCTTTAGTAGATTGAATTGGTTGACCCACTTAAAATTCAAATACCCAGCATTGAACGTGACTATGCCAAACAATGAAAAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGGGTACGGACAATGACCAAATCTTCCCGTATGCTCAAGCATCAGGAAGAATCACAGTCTCTACCAAAAGAAGCCAACAAACTGTAATCCCGAATATCGGATCTAGACCCAGAGTAAGGAATATCCCCAGCAGAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCTCCTAGGGGTTACTTCAAAATACGAAGTGGGAAAAGCTCAATAATGAGATCAGATGCACCCATTGGCAAATGCAATTCTGAATGCATCACTCCAAACGGAAGCATTCCCAATGACAAACCATTCCAAAATGTAAACAGGATCACATACGGGGCCTGTCCCAGATATGTTAAGCAAAACACTCTGAAATTGGCAACAGGGATGCGAAATGTACCAGAGAAACAAACTAGAGGCATATTTGGCGCAATCGCGGGTTTCATAGAAAATGGTTGGGAGGGAATGGTGGATGGTTGGTACGGTTTCAGGCATCAAAATTCTGAGGGAATAGGACAAGCAGCAGATCTCAAAAGCACTCAAGCAGCAATCGATCAAATCAATGGGAAGCTGAATAGGTTGATCGGGAAAACCAACGAGAAATTCCATCAGATTGAAAAAGAATTCTCAGAAGTCGAAGGGAGAATTCAGGACCTTGAGAAATATGTTGAGGACACCAAAATAGATCTCTGGTCATACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATCTAACTGACTCAGAAATGAACAAACTGTTTGAAAAAACAAAGAAGCAACTGAGGGAAAATGCTGAGGATATGGGCAATGGTTGTTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCACAATGTATACAGAGATGAAGCATTAAACAACCGGTTCCAGATCAAGGGCGTTGAGCTGAAGTCAGGATACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGTTTTTTGCTTTGTGTTGCTTTGTTGGGGTTCATCATGTGGGCCTGCCAAAAAGGCAACATTAGGTGCAACATTTGCATTTGA"
				},	{
					"strain": "A/Perth/16/2009",
					"db": "IRD",
					"accession": "GQ293081",
					"date": "2009-04-07",
					"seq": "ATGAAGACTATCATTGCTTTGAGCTACATTCTATGTCTGGTTTTCGCTCAAAAACTTCCTGGAAATGACAACAGCACGGCAACGCTGTGCCTTGGGCACCATGCAGTACCAAACGGAACGATAGTGAAAACAATCACGAATGACCAAATTGAAGTTACTAATGCTACTGAGCTGGTTCAGAGTTCCTCAACAGGTGAAATATGCGACAGTCCTCATCAGATCCTTGATGGAAAAAACTGCACACTAATAGATGCTCTATTGGGAGACCCTCAGTGTGATGGCTTCCAAAATAAGAAATGGGACCTTTTTGTTGAACGCAGCAAAGCCTACAGCAACTGTTACCCTTATGATGTGCCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCCGGCACACTGGAGTTTAACAATGAAAGCTTCAATTGGACTGGAGTCACTCAAAACGGAACAAGCTCTGCTTGCATAAGGAGATCTAAAAACAGTTTCTTTAGTAGATTGAATTGGTTGACCCACTTAAACTTCAAATACCCAGCATTGAACGTGACTATGCCAAACAATGAACAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGGGTACGGACAAAGACCAAATCTTCCTGTATGCTCAAGCATCAGGAAGAATCACAGTCTCTACCAAAAGAAGCCAACAAACCGTAAGCCCGAATATCGGATCTAGACCCAGAGTAAGGAATATCCCTAGCAGAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCTCCTAGGGGTTACTTCAAAATACGAAGTGGGAAAAGCTCAATAATGAGATCAGATGCACCCATTGGCAAATGCAATTCTGAATGCATCACTCCAAATGGAAGCATTCCCAATGACAAACCATTCCAAAATGTAAACAGGATCACATACGGGGCCTGTCCCAGATATGTTAAGCAAAACACTCTGAAATTGGCAACAGGGATGCGAAATGTACCAGAGAAACAAACTAGAGGCATATTTGGCGCAATCGCGGGTTTCATAGAAAATGGTTGGGAGGGAATGGTGGATGGTTGGTACGGTTTCAGGCATCAAAATTCTGAGGGAAGAGGACAAGCAGCAGATCTCAAAAGCACTCAAGCAGCAATCGATCAAATCAATGGGAAGCTGAATAGATTGATCGGGAAAACCAACGAGAAATTCCATCAGATTGAAAAAGAATTCTCAGAAGTCGAAGGGAGAATTCAGGACCTTGAGAAATATGTTGAGGACACTAAAATAGATCTCTGGTCATACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATCTAACTGACTCAGAAATGAACAAACTGTTTGAAAAAACAAAGAAGCAACTGAGGGAAAATGCTGAGGATATGGGCAATGGTTGTTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCACGATGTATACAGAGATGAAGCATTAAACAACCGGTTTCAGATCAAGGGAGTTGAGCTGAAGTCAGGGTACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGTTTTTTGCTTTGTGTTGCTTTGTTGGGGTTCATCATGTGGGCCTGCCAAAAAGGCAACATTAGGTGCAACATTTGCATTTGA"
				},	{
					"strain": "A/Victoria/361/2011",
					"db": "IRD",
					"accession": "GQ293081",
					"date": "2011-10-24",
					"seq": "ATGAAGACTATCATTGCTTTGAGCCACATTCTATGTCTGGTTTTCGCTCAAAAACTTCCTGGAAATGACAACAGCACGGCAACGCTGTGCCTTGGGCACCATGCAGTACCAAACGGAACGATAGTGAAAACAATCACGAATGACCAAATTGAAGTTACTAATGCTACTGAGCTGGTTCAGAATTCCTCAATAGGTGAAATATGCGACAGTCCTCATCAGATCCTTGATGGAGAAAACTGCACACTAATAGATGCTCTATTGGGAGACCCTCAGTGTGATGGCTTCCAAAATAAGAAATGGGACCTTTTTGTTGAACGAAGCAAAGCCTACAGCAACTGTTACCCTTATGATGTGCCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCCGGCACACTGGAGTTTAACAATGAAAGCTTCAATTGGACTGGAGTCACTCAAAACGGAACAAGTTCTGCTTGCATAAGGAGATCTAATAATAGTTTCTTTAGTAGATTAAATTGGTTGACCCGCTTAAACTTCAAATACCCAGCATTGAACGTGACTATGCCAAACAATGAACAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGGTTACGGACAAGGAACAAATCTTCCTGTATGCTCAATCATCAGGAAGAATCACAGTATCTACCAAAAGAAGCCAACAAGCTGTAATCCCGAATATCGGATATAGACCCAGAATAAGGAATATCCCTAGCAGAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCTCCTAGGGGTTACTTCAAAATACGAAGTGGGAAAAGCTCAATAATGAGATCAGATGCACCCATTGGCAAATGCAATTCTGAATGCATCACTCCAAATGGAAGCATTCCCAATGACAAACCATTCCAAAATGTAAACAGGATCACATACGGGGCCTGTCCCAGATATGTTAAGCAAAGCACTCTGAAATTGGCAACAGGAATGCGAAATGTACCAGAGAAACAAACTAGAGGCATATTTGGCGCAATAGCGGGTTTCATAGAAAATGGTTGGGAGGGAATGGTGGATGGTTGGTACGGTTTCAGGCATCAAAATTCTGAGGGAAGAGGACAAGCAGCAGATCTCAAAAGCACTCAAGCAGCAATCGATCAAATCAATGGGAAGCTGAATCGATTGATCGGGAAAACCAACGAGAAATTCCATCAGATTGAAAAAGAATTCTCAGAAGTCGAAGGGAGAATTCAGGACCTTGAGAAATATGTTGAGGACACTAAAATAGATCTCTGGTCATACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATCTAACTGACTCAGAAATGAACAAACTGTTTGAAAAAACAAAGAAGCAACTAAGGGAAAATGCTGAGGATATGGGCAATGGTTGTTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCACGATGTATACAGAGATGAAGCATTAAACAACCGGTTCCAGATCAAGGGAGTTGAGCTGAAGTCAGGGTACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGTTTTTTGCTTTGTGTTGCTTTGTTGGGGTTCATCATGTGGGCCTGCCAAAAGGGCAACATTAGGTGCAACATTTGCATTTGA"
				},	{
					"strain": "A/Texas/50/2012",
					"db": "GISAID",
					"accession": "EPI_ISL_129858",
					"date": "2012-04-15",
					"seq": "ATGAAGACTATCATTGCTTTGAGCTACATTCTATGTCTGGTTTTCGCTCAAAAACTTCCTGGAAATGACAATAGCACGGCAACGCTGTGCCTTGGGCACCATGCAGTACCAAACGGAACGATAGTGAAAACAATCACGAATGACCGAATTGAAGTTACTAATGCTACTGAACTGGTTCAGAATTCCTCAATAGGTGAAATATGCGACAGTCCTCATCAGATCCTTGATGGAGAAAACTGCACACTAATAGATGCTCTATTGGGAGACCCTCAGTGTGATGGCTTCCAAAATAAGAAATGGGACCTTTTTGTTGAACGAAGCAAAGCCTACAGCAACTGTTACCCTTATGATGTGCCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCCGGCACACTGGAGTTTAACAATGAAAGCTTCAATTGGAATGGAGTCACTCAAAACGGAACAAGTTCTGCTTGCATAAGGAGATCTAATAATAGTTTCTTTAGTAGATTAAATTGGTTGACCCACTTAAACTTCAAATACCCAGCATTGAACGTGACTATGCCAAACAATGAACAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGGGTACGGACAAGGACCAAATCTTCCTGTATGCTCAACCATCAGGAAGAATCACAGTATCTACCAAAAGAAGCCAACAAGCTGTAATCCCGAATATCGGATCTAGACCCAGAATAAGGAATATCCCTAGCAGAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCTCCTAGGGGTTACTTCAAAATACGAAGTGGGAAAAGCTCAATAATGAGATCAGATGCACCCATTGGCAAATGCAAGTCTGAATGCATCACTCCAAATGGAAGCATTCCCAATGACAAACCATTCCAAAATGTAAACAGGATCACATACGGGGCCTGTCCCAGATATGTTAAGCAAAGCACTCTGAAATTGGCAACAGGAATGCGGAATGTACCAGAGAAACAAACTAGAGGCATATTTGGCGCAATAGCGGGTTTCATAGAAAATGGTTGGGAGGGAATGGTGGATGGTTGGTACGGTTTCAGGCATCAAAATTCTGAGGGAAGAGGACAAGCAGCAGATCTCAAAAGCACTCAAGCAGCAATCGATCAAATCAATGGGAAGCTGAATCGATTGATCGGGAAAACCAACGAGAAATTCCATCAGATTGAAAAAGAATTCTCAGAAGTAGAAGGGAGAATTCAGGACCTTGAGAAATATGTTGAGGACACTAAAATAGATCTCTGGTCATACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATCTAACTGACTCAGAAATGAACAAACTGTTTGAAAAAACAAAGAAGCAACTGAGGGAAAATGCTGAGGATATGGGCAATGGTTGTTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCACGATGTATACAGAGATGAAGCATTAAACAACCGGTTCCAGATCAAGGGAGTTGAGCTGAAGTCAGGGTACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGTTTTTTGCTTTGTGTTGCTTTGTTGGGGTTCATCATGTGGGCCTGCCAAAAGGGCAACATTAGGTGCAACATTTGCATTTGA",
				},	{
					"strain": "A/Switzerland/9715293/2013",
					"db": "GISAID",
					"accession": "EPI_ISL_162149",
					"date": "2013-12-06",
					"seq": "ATGAAGACTATCATTGCTTTGAGCTACATTCTATGTCTGGTTTTCGCTCAAAAACTTCCTGGAAATGACAATAGCACGGCAACGCTGTGCCTTGGGCACCATGCAGTACCAAACGGAACGATAGTGAAAACAATCACGAATGACCGAATTGAAGTTACTAATGCTACTGAGCTGGTTCAGAATTCCTCAATAGGTGAAATATGCGACAGTCCTCATCAGATCCTTGATGGAGAAAACTGCACACTAATAGATGCTCTATTGGGAGACCCTCAGTGTGATGGCTTTCAAAATAAGAAATGGGACCTTTTTGTTGAACGAAGCAAAGCCTACAGCAACTGTTACCCTTATGATGTGCCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCCGGCACACTGGAGTTTAACAATGAAAGCTTCAATTGGGCTGGAGTCACTCAAAACGGAACAAGTTCTTCTTGCATAAGGGGATCTAATAGTAGTTTCTTTAGTAGATTAAATTGGTTGACCCACTTAAACTCCAAATACCCAGCATTAAACGTGACTATGCCAAACAATGAACAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGGGTACGGACAAGGACCAAATCTTCCTGTATGCACAATCATCAGGAAGAATCACAGTATCTACCAAAAGAAGCCAACAAGCTGTAATCCCGAATATCGGATCTAGACCCAGAATAAGGGATATCCCTAGCAGAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCTCCTAGGGGTTACTTCAAAATACGAAGTGGGAAAAGCTCAATAATGAGATCAGATGCACCCATTGGCAAATGCAAGTCTGAATGCATCACTCCAAATGGAAGCATTCCCAATGACAAACCATTCCAAAATGTAAACAGGATCACATACGGGGCCTGTCCCAGATATGTTAAGCAAAGCACTCTGAAATTGGCAACAGGAATGCGAAATGTACCAGAGAGACAAACTAGAGGCATATTTGGCGCAATAGCGGGTTTCATAGAAAATGGTTGGGAGGGAATGGTGGATGGTTGGTACGGCTTCAGGCATCAAAATTCTGAGGGAAGAGGACAAGCAGCAGATCTCAAAAGCACTCAAGCAGCAATCGATCAAATCAATGGGAAGCTGAATCGATTGATCGGGAAAACCAACGAGAAATTCCATCAGATTGAAAAAGAATTCTCAGAAGTAGAAGGGAGAATTCAGGACCTTGAGAAATATGTTGAGGACACAAAAATAGATCTCTGGTCATACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATCTAACTGACTCAGAAATGAACAAACTGTTTGAAAAAACAAAGAAGCAACTGAGGGAAAATGCTGAGGATATGGGCAATGGTTGTTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCACGATGTATACAGGGATGAAGCATTAAACAACCGGTTCCAGATCAAGGGAGTTGAGCTGAAGTCAGGGTACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGTTTTTTGCTTTGTGTTGCTTTGTTGGGGTTCATCATGTGGGCCTGCCAAAAGGGCAACATTAGGTGCAACATTTGCATTTGA",
				}
			]
		self.outgroup = {
			'strain': 'A/Beijing/32/1992',
			'db': 'IRD',
			'accession': 'U26830',
			'date': '1992-01-01',
			'country': 'China',
			'region': 'China',
			'seq': 'ATGAAGACTATCATTGCTTTGAGCTACATTTTATGTCTGGTTTTCGCTCAAAAACTTCCCGGAAATGACAACAGCACAGCAACGCTGTGCCTGGGACATCATGCAGTGCCAAACGGAACGCTAGTGAAAACAATCACGAATGATCAAATTGAAGTGACTAATGCTACTGAGCTGGTTCAGAGTTCCTCAACAGGTAGAATATGCGACAGTCCTCACCGAATCCTTGATGGAAAAAACTGCACACTGATAGATGCTCTATTGGGAGACCCTCATTGTGATGGCTTCCAAAATAAGGAATGGGACCTTTTTGTTGAACGCAGCAAAGCTTACAGCAACTGTTACCCTTATGATGTACCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCAGGCACCCTGGAGTTTATCAATGAAGACTTCAATTGGACTGGAGTCGCTCAGGATGGGGGAAGCTATGCTTGCAAAAGGGGATCTGTTAACAGTTTCTTTAGTAGATTGAATTGGTTGCACAAATCAGAATACAAATATCCAGCGCTGAACGTGACTATGCCAAACAATGGCAAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGAGCACGGACAGAGACCAAACCAGCCTATATGTTCGAGCATCAGGGAGAGTCACAGTCTCTACCAAAAGAAGCCAACAAACTGTAACCCCGAATATCGGGTCTAGACCCTGGGTAAGGGGTCAGTCCAGTAGAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAATAGCACAGGGAATCTAATTGCTCCTCGGGGTTACTTCAAAATACGAAATGGGAAAAGCTCAATAATGAGGTCAGATGCACCCATTGGCACCTGCAGTTCTGAATGCATCACTCCAAATGGAAGCATTCCCAATGACAAACCTTTTCAAAATGTAAACAGGATCACATATGGGGCCTGCCCCAGATATGTTAAGCAAAACACTCTGAAATTGGCAACAGGGATGCGGAATGTACCAGAGAAACAAACTAGAGGCATATTCGGCGCAATCGCAGGTTTCATAGAAAATGGTTGGGAGGGAATGGTAGACGGTTGGTACGGTTTCAGGCATCAAAATTCTGAGGGCACAGGACAAGCAGCAGATCTTAAAAGCACTCAAGCAGCAATCGACCAAATCAACGGGAAACTGAATAGGTTAATCGAGAAAACGAACGAGAAATTCCATCAAATCGAAAAAGAATTCTCAGAAGTAGAAGGGAGAATTCAGGACCTCGAGAAATATGTTGAAGACACTAAAATAGATCTCTGGTCTTACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATCTTACTGACTCAGAAATGAACAAACTGTTTGAAAAAACAAGGAAGCAACTGAGGGAAAATGCTGAGGACATGGGCAATGGTTGCTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGGTCAATCAGAAATGGAACTTATGACCATGATGTATACAGAGACGAAGCATTAAACAACCGGTTCCAGATCAAAGGTGTTGAGCTGAAGTCAGGATACAAAGATTGGATCCTGTGGATTTCCTTTGCCATATCATGCTTTTTGCTTTGTGTTGTTTTGCTGGGGTTCATCATGTGGGCCTGCCAAAAAGGCAACATTAGGTGTAACATTTGCATTTGA'
		}

class H3N2_clean(virus_clean):
	def __init__(self,**kwargs):
		virus_clean.__init__(self, **kwargs)

	def clean_outbreaks(self):
		"""Remove duplicate strains, where the geographic location, date of sampling and sequence are identical"""
		virus_hashes = set()
		new_viruses = []
		for v in self.viruses:
			geo = re.search(r'A/([^/]+)/', v.strain).group(1)
			if geo:
				vhash = (geo, v.date, str(v.seq))
				if vhash not in virus_hashes:
					new_viruses.append(v)
					virus_hashes.add(vhash)

		self.viruses = MultipleSeqAlignment(new_viruses)

	def clean_reassortants(self):
		from seq_util import hamming_distance as distance
		"""Remove viruses from the outbreak of triple reassortant pH1N1"""
		remove_viruses = []
		
		reassortant_seq = "ATGAAGACTATCATTGCTTTTAGCTGCATTTTATGTCTGATTTTCGCTCAAAAACTTCCCGGAAGTGACAACAGCATGGCAACGCTGTGCCTGGGACACCATGCAGTGCCAAACGGAACATTAGTGAAAACAATCACGGATGACCAAATTGAAGTGACTAATGCTACTGAGCTGGTCCAGAGTTCCTCAACAGGTGGAATATGCAACAGTCCTCACCAAATCCTTGATGGGAAAAATTGCACACTGATAGATGCTCTATTGGGGGACCCTCATTGTGATGACTTCCAAAACAAGGAATGGGACCTTTTTGTTGAACGAAGCACAGCCTACAGCAACTGTTACCCTTATTACGTGCCGGATTATGCCACCCTTAGATCATTAGTTGCCTCATCCGGCAACCTGGAATTTACCCAAGAAAGCTTCAATTGGACTGGAGTTGCTCAAGGCGGATCAAGCTATGCCTGCAGAAGGGGATCTGTTAACAGTTTCTTTAGTAGATTGAATTGGTTGTATAACTTGAATTACAAGTATCCAGAGCAGAACGTAACTATGCCAAACAATGACAAATTTGACAAATTGTACATTTGGGGGGTTCACCACCCGGGTACGGACAAGGACCAAACCAACCTATATGTCCAAGCATCAGGGAGAGTTATAGTCTCTACCAAAAGAAGCCAACAAACTGTAATCCCGAATATCGGGTCTAGACCCTGGGTAAGGGGTGTCTCCAGCATAATAAGCATCTATTGGACGATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCCCCTCGGGGTTACTTCAAAATACAAAGTGGGAAAAGCTCAATAATGAGATCAGATGCACACATTGATGAATGCAATTCTGAATGCATTACTCCAAATGGAAGCATTCCCAATGACAAACCTTTTCAAAATGTAAACAAGATCACATATGGAGCCTGTCCCAGATATGTTAAGCAAAACACCCTGAAATTGGCAACAGGAATGCGGAATGTACCAGAGAAACAAACTAGAGGCATATTCGGCGCAATTGCAGGTTTCATAGAAAATGGTTGGGAGGGAATGGTAGACGGTTGGTACGGTTTCAGGCATCAGAATTCTGAAGGCACAGGACAAGCAGCAGATCTTAAAAGCACTCAAGCAGCAATCAACCAAATCACCGGGAAACTAAATAGAGTAATCAAGAAAACAAACGAGAAATTCCATCAAATCGAAAAAGAATTCTCAGAAGTAGAAGGAAGAATTCAGGACCTAGAGAAATACGTTGAAGACACTAAAATAGATCTCTGGTCTTACAACGCTGAGATTCTTGTTGCCCTGGAGAACCAACATACAATTGATTTAACCGACTCAGAGATGAGCAAACTGTTCGAAAGAACAAGAAGGCAACTGCGGGAAAATGCTGAGGACATGGGCAATGGTTGCTTCAAAATATACCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCATGATATATACAGAAACGAGGCATTAAACAATCGGTTCCAGATCAAAGGTGTTCAGCTAAAGTCAGGATACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGCTTTTTGCTTTGTGTTGTTCTGCTGGGGTTCATTATGTGGGCCTGCCAAAAAGGCAACATTAGGTGCAACATTTGCATTTGA"
		for v in self.viruses:
			dist = distance(Seq(reassortant_seq), v)
			if (dist < 0.02):
				remove_viruses.append(v)
				if self.verbose>1:
					print "\t\tremoving",v.strain

		reassortant_seq = "ATGAAGACTATCATTGCTTTTAGCTGCATCTTATGTCAGATCTCCGCTCAAAAACTCCCCGGAAGTGACAACAGCATGGCAACGCTGTGCCTGGGGCATCACGCAGTACCAAACGGAACGTTAGTGAAAACAATAACAGATGACCAAATTGAAGTGACTAATGCTACTGAGCTGGTCCAGAGTACCTCAAAAGGTGAAATATGCAGTAGTCCTCACCAAATCCTTGATGGAAAAAATTGTACACTGATAGATGCTCTATTGGGAGACCCTCATTGTGATGACTTCCAAAACAAGAAATGGGACCTTTTTGTTGAACGAAGCACAGCTTACAGCAACTGTTACCCTTATTATGTGCCGGATTATGCCTCCCTTAGGTCACTAGTTGCCTCATCCGGCACCCTGGAATTTACTCAAGAAAGCTTCAATTGGACTGGGGTTGCTCAAGACGGAGCAAGCTATTCTTGCAGAAGGGAATCTGAAAACAGTTTCTTTAGTAGATTGAATTGGTTATATAGTTTGAATTACAAATATCCAGCGCTGAACGTAACTATGCCAAACAATGACAAATTTGACAAATTGTACATTTGGGGGGTACACCACCCGGGTACGGACAAGGACCAAACCAGTCTATATATTCAAGCATCAGGGAGAGTTACAGTCTCCACCAAATGGAGCCAACAAACTGTAATCCCGAATATCGGGTCTAGACCCTGGATAAGGGGTGTCTCCAGCATAATAAGCATCTATTGGACAATAGTAAAACCGGGAGACATACTTTTGATTAACAGCACAGGGAATCTAATTGCCCCTCGGGGTTACTTCAAAATACAAAGTGGGAAAAGCTCAATAATGAGGTCAGATGCACACATTGGCAACTGCAACTCTGAATGCATTACCCCAAATGGAAGCATTCCCAACGACAAACCTTTTCAAAATGTAAACAGAATAACATATGGGGCCTGTCCCAGATATGTTAAGCAAAACACTCTGAAATTAGCAACAGGAATGCGGAATGTACCAGAGAAACAAACTAGAGGCATATTCGGCGCAATCGCAGGTTTCATAGAAAATGGTTGGGAAGGGATGGTGGACGGTTGGTATGGTTTCAGGCATCAAAACTCTGAAGGCACAGGGCAAGCAGCAGATCTTAAAAGCACTCAAGCGGCAATCAACCAAATCACCGGGAAACTAAATAGAGTAATCAAGAAGACGAATGAAAAATTCCATCAGATCGAAAAAGAATTCTCAGAAGTAGAAGGGAGAATTCAGGACCTAGAGAGATACGTTGAAGACACTAAAATAGACCTCTGGTCTTACAACGCGGAGCTTCTTGTTGCCCTGGAGAACCAACATACAATTGATTTAACTGACTCAGAAATGAACAAACTGTTCGAAAGGACAAGGAAGCAACTGCGGGAAAATGCTGAGGACATGGGCAATGGATGCTTTAAAATATATCACAAATGTGACAATGCCTGCATAGGATCAATCAGAAATGGAACTTATGACCATGATGTATACAGAGACGAAGCAGTAAACAATCGGTTCCAGATCAAAGGTGTTCAGCTGAAGTTAGGATACAAAGATTGGATCCTATGGATTTCCTTTGCCATATCATGCTTTTTGCTTTGTGCTGTTCTGCTAGGATTCATTATGTGGGCATGCCAAAAAGGCAACATTAGGTGCAACATTTGCATTTGA"
		for v in self.viruses:
			dist = distance(Seq(reassortant_seq), v)
			if (dist < 0.02):
				remove_viruses.append(v)
				if self.verbose>1:
					print "\t\tremoving",v.strain

		reassortant_seq = "ATGAAGACTAGTAGTTCTGCTATATACATTGCAA------------------------CCGCAAATG---------CAGACACATTATGTATAGGTTATCATGCAGTACTAGAAAAGAATGTAACAGTAACACACTCTGTTAACCAAACTGAGAGGGGTAGCCCCATTGCATTTG--------------------GGTAAATGTAACATTGCTGGCTGGATCC------------------------------------TGGGAAATCCAGAGTGTGACACTCTCCACAGCAAGCTCATGGTCCTACATCGTGGAAACATCTAAGACAATGGAACGTGCTACCCAGGAGATTTCATCAATTATGAGGAGCTAAGGTCATCATTTGAAAGGTTTGAGATATTACAAGTTCATGGCCCAATCATGACTCGAACAAAGGTTCCTCAAGCTGGAGCAA---------------------------AAAGCTTCTACAAAAATTTAATATGGCTAGTTAAAAAAGGAAATTCATACCCAA------------------------------AGCTCAGCAAATCCTACATTTGGGGCATTCACCATCCATCTACTAGTGCTGACCAA-------CAAAGTCTCTATCAGAGTGCAGATGCATATGTTTTATCAAAATACAGCAAGAAGTTCAAG--CCGGAAATAGCAGTAAGACCCAAAGTGAGGGATCAAGAAGGGAGAATGAACTATTACTGGACACTAGTAGAGCCGGGAGACAAAATAACATTCGAAGCAACTGGAAATCTATTGGTACCGAGATATGCATTCGCAATGGAAA----GAAATGCTGGATTATCATTTCAGATACACCAGTCCACGATTGCAATACAACTTGTCAGACACCCAAGGGTGCTATAAACACCAGCCTCCCATTTCAGAATATACATCCGATCACAATTGGAAAATGTCCCAAATATGTAAAAAGCACAAAATTGAGACTGGCCACAGGATTGAGGAATGTCCCGTCTATTCAATCTAGAGGCCTATTTGGGGCCATTGCCGGTTTCATTGAAGGGGGGTGGACAGGGATGGTAGATGGATGGTACGGTTATCACCATCAAAATGCGCAGGGGTCAGGATATGCAGCCGACCTGAAGAGCACACAGAATGCCATTGACAAGATTACTAACAAAGTAAATTCTGTTATTGAAAAGATGAATACACAGTTCACAGCAGTAGGTAAAGAGTTCAACCACCTGGAAAAAAGAATAGAGAATTTAAATAAAAAAGTTGATGATGGTTTCCTGGACATTTGGACTTACAATGCCGAACTGTTGGTTCTATTGGAAAATGAAAGAACTTTGGACTACCACGATTCAAATGTGAAAAACTTATATGAAAAGGTAAGAAGCCAGTTAAAAAACAATGCCAAGGAAATTGGAAACGGCTGCTTTGAATTTTACCACAAATGCGATAACACGTGCATGGAAAGTGTCAAAAATGGGACTTATGACTACCCAAAATACTCAGAGGAAGCAAAATTAAACAGAGAAGAAATAGATGGGGTAAAGCTGGAATCAACAAGGATTTACCAGATTTTGGCGATCTATTCAACTGTCGCCAGTTCATTGGTACTGGTAGTCTCCCTGGGGGCAATCATCTGGATGTGCTCTAATGGGTCTCTACAGTGTAGAATATGTATTTAA"
		for v in self.viruses:
			dist = distance(Seq(reassortant_seq), v)
			if (dist < 0.02):
				remove_viruses.append(v)
				if self.verbose>1:
					print "\t\tremoving",v.strain

		self.viruses = MultipleSeqAlignment([v for v in self.viruses if v not in remove_viruses])

	def clean(self):
		self.clean_generic()
		self.clean_outbreaks()
		print "Number of viruses after outbreak filtering:",len(self.viruses)
		self.clean_reassortants()
		print "Number of viruses after reassortant filtering:",len(self.viruses)


class H3N2_refine(tree_refine):
	def __init__(self, **kwargs):
		tree_refine.__init__(self, **kwargs)

	def refine(self):
		self.refine_generic()  # -> all nodes now have aa_seq, xvalue, yvalue, trunk, and basic virus properties
		self.add_H3N2_attributes()

	def epitope_sites(self, aa):
		aaa = np.fromstring(aa, 'S1')
		return ''.join(aaa[epitope_mask[:len(aa)]=='1'])

	def nonepitope_sites(self, aa):
		aaa = np.fromstring(aa, 'S1')
		return ''.join(aaa[epitope_mask[:len(aa)]=='0'])

	def receptor_binding_sites(self, aa):
		'''
		Receptor binding site mutations from Koel et al. 2014
		These are (145, 155, 156, 158, 159, 189, 193) in canonical HA numbering
		need to subtract one since python arrays start at 0
		'''
		sites = [144, 154, 155, 157, 158, 188, 192]
		return ''.join([aa[pos] for pos in sites])

	def get_HA1(self, aa):
		'''
		return the part of the peptide corresponding to HA1, starts is 329 aa long
		'''
		return aa[:329]

	def epitope_distance(self, aaA, aaB):
		"""Return distance of sequences aaA and aaB by comparing epitope sites"""
		epA = self.epitope_sites(aaA)
		epB = self.epitope_sites(aaB)
		distance = sum(a != b for a, b in izip(epA, epB))
		return distance

	def nonepitope_distance(self, aaA, aaB):
		"""Return distance of sequences aaA and aaB by comparing non-epitope sites"""
		neA = self.nonepitope_sites(aaA)
		neB = self.nonepitope_sites(aaB)
		distance = sum(a != b for a, b in izip(neA, neB))
		return distance

	def receptor_binding_distance(self, aaA, aaB):
		"""Return distance of sequences aaA and aaB by comparing receptor binding sites"""
		neA = self.receptor_binding_sites(aaA)
		neB = self.receptor_binding_sites(aaB)
		distance = sum(a != b for a, b in izip(neA, neB))
		return distance

	def add_H3N2_attributes(self):
		root = self.tree.seed_node
		for node in self.tree.postorder_node_iter():
			node.ep = self.epitope_distance(node.aa_seq, root.aa_seq)
			node.ne = self.nonepitope_distance(node.aa_seq, root.aa_seq)
			node.rb = self.receptor_binding_distance(node.aa_seq, root.aa_seq)

		for v in self.viruses:
			if v.strain in self.node_lookup:
				node = self.node_lookup[v.strain]
				try:
					node.passage=v.passage
				except:
					pass

class H3N2_process(process, H3N2_filter, H3N2_clean, H3N2_refine, HI_tree, fitness_model):
	"""docstring for H3N2_process, H3N2_filter"""
	def __init__(self,verbose = 0, force_include = None, 
				force_include_all = False, max_global= True, **kwargs):
		self.force_include = force_include
		self.force_include_all = force_include_all
		self.max_global = max_global
		process.__init__(self, **kwargs)
		H3N2_filter.__init__(self,**kwargs)
		H3N2_clean.__init__(self,**kwargs)
		H3N2_refine.__init__(self,**kwargs)
		HI_tree.__init__(self,**kwargs)
		fitness_model.__init__(self,**kwargs)
		self.verbose = verbose

	def run(self, steps, years_back=3, viruses_per_month=50, raxml_time_limit = 1.0, reg = 2):
		if 'filter' in steps:
			print "--- Virus filtering at " + time.strftime("%H:%M:%S") + " ---"
			self.filter()
			if self.force_include is not None and os.path.isfile(self.force_include):
				with open(self.force_include) as infile:
					forced_strains = [line.strip().lower() for line in infile]
			else:
				forced_strains = []
			self.subsample(years_back, viruses_per_month, 
				prioritize=forced_strains, all_priority=self.force_include_all, 
				region_specific = self.max_global)
			self.dump()
		else:
			self.load()
		if 'align' in steps:
			self.align()   	# -> self.viruses is an alignment object
		if 'clean' in steps:
			print "--- Clean at " + time.strftime("%H:%M:%S") + " ---"
			self.clean()   # -> every node as a numerical date
			self.dump()
		if 'tree' in steps:
			print "--- Tree	 infer at " + time.strftime("%H:%M:%S") + " ---"
			self.infer_tree(raxml_time_limit)  # -> self has a tree
			self.dump()
		if 'ancestral' in steps:
			print "--- Infer ancestral sequences " + time.strftime("%H:%M:%S") + " ---"
			self.infer_ancestral()  # -> every node has a sequence
		if 'refine' in steps:
			print "--- Tree refine at " + time.strftime("%H:%M:%S") + " ---"
			self.refine()
			self.dump()
		if 'frequencies' in steps:
			print "--- Estimating frequencies at " + time.strftime("%H:%M:%S") + " ---"
			self.determine_variable_positions()
			self.estimate_frequencies()
			self.dump()
		if 'HI' in steps:
			print "--- Adding HI titers to the tree " + time.strftime("%H:%M:%S") + " ---"
			self.map_HI_to_tree(training_fraction=0.9, method = 'nnl1reg', lam_HI=reg, lam_avi=reg, lam_pot = reg)
			self.add_titers()
			self.dump()
#		if 'fitness' in steps:


		if 'export' in steps:
			self.temporal_regional_statistics()
			# exporting to json, including the H3N2 specific fields
			self.export_to_auspice(tree_fields = ['ep', 'ne', 'rb', 'dHI', 'cHI', 'HI_titers', 'serum', 'HI_info', 'avidity', 'potency'])

if __name__=="__main__":
	all_steps = ['filter', 'align', 'clean', 'tree', 'ancestral', 'refine', 'frequencies', 'HI', 'export']
	parser = argparse.ArgumentParser(description='Process virus sequences, build tree, and prepare of web visualization')
	parser.add_argument('-y', '--years_back', type = int, default=3, help='number of past years to sample sequences from')
	parser.add_argument('-v', '--viruses_per_month', type = int, default = 50, help='number of viruses sampled per month')
	parser.add_argument('-r', '--raxml_time_limit', type = float, default = 1.0, help='number of hours raxml is run')
	parser.add_argument('--prefix', type = str, default = 'data/', help='path+prefix of file dumps')
	parser.add_argument('--test', default = False, action="store_true",  help ="don't run the pipeline")
	parser.add_argument('--start', default = 'filter', type = str,  help ="start pipeline at virus selection")
	parser.add_argument('--stop', default = 'export', type=str,  help ="run to end")
	params = parser.parse_args()
	params.cds = (48,None)

	steps = all_steps[all_steps.index(params.start):(all_steps.index(params.stop)+1)]
	# add all arguments to virus_config (possibly overriding)
	virus_config.update(params.__dict__)
	# pass all these arguments to the processor: will be passed down as kwargs through all classes
	myH3N2 = H3N2_process(**virus_config) 
	if params.test:
		myH3N2.load()
	else:
		myH3N2.run(steps, years_back=virus_config['years_back'], 
			viruses_per_month = virus_config['viruses_per_month'], 
			raxml_time_limit = virus_config['raxml_time_limit'])
