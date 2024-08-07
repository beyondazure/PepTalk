#txtreader.py
import sys, math, os, re
import numpy as np
import statistics as stats

print("""
███████████                     ███████████           ████  █████
░░███░░░░░███                   ░█░░░███░░░█          ░░███ ░░███
 ░███    ░███  ██████  ████████ ░   ░███  ░   ██████   ░███  ░███ █████
 ░██████████  ███░░███░░███░░███    ░███     ░░░░░███  ░███  ░███░░███
 ░███░░░░░░  ░███████  ░███ ░███    ░███      ███████  ░███  ░██████░
 ░███        ░███░░░   ░███ ░███    ░███     ███░░███  ░███  ░███░░███
 █████       ░░██████  ░███████     █████   ░░████████ █████ ████ █████
░░░░░         ░░░░░░   ░███░░░     ░░░░░     ░░░░░░░░ ░░░░░ ░░░░ ░░░░░
                       ░███
                       █████
                      ░░░░░                                            \n""")
print("""\n* * * * * * * * A PEPTIDE MASS-SPEC DATA ANALYSIS TOOL * * * * * * * *\n""")

#Reading in command-line arguments into a list
argument_list = sys.argv[1:]

#Setting default values (to throw errors if user does not provide input/output file name)
filename = "0"
output_name = "0"

#Parsing command-line arguments and searching for predefined flags
try:
    for arg in argument_list:
        if arg in ("-h"):
            print("\nUsage: peptalk [option] -i [input file] -o [output file] -p [JSON params file]")
            print("""\nOptions and arguments: \n-h\t: print the usage manual\n-i\t: name of the input file (currently tab-delimited text only)\n-o\t: name of the output file\n-p\t: path to a JSON custom analysis parameters file\n-v\t: verbose output\n-c\t: parse a cysteine reactivity file""")
            quit()
        if arg in ("-o"):
            #Searching for filename (next item after the flag)
            for i in range(len(argument_list)):
                if argument_list[i] == "-o":
                    output_name = argument_list[i+1]
        if arg in ("-i"):
            for i in range(len(argument_list)):
                if argument_list[i] == "-i" and i != len(argument_list):
                    filename = argument_list[i+1]
        #elif curr_arg in ("-p"):
        #elif curr_arg in ("-v"):
        #elif curr_arg in ("-c"):
#Throwing exceptions
except:
    print("Could not load arguments")
    quit()

if filename == "0":
    print("\nInput file name not provided\n")
    quit()

if output_name == "0":
    print("\nOutput file name not provided\n")
    quit()

#Opening the provided text file and extracting the text
sheet = open(filename, "r")
text = sheet.read()
sheet.close()

#Stripping the text of the redundant quotation marks and writing the processed text into original file
text_stripped = text.replace('"','')
sheet2 = open(filename, "w")
sheet2.write(text_stripped)
sheet2.close()

#Loading the processed text
sheet3 = open(filename, "r")
content = sheet3.readlines()
sheet3.close()

#Extracting and sanitizing the header line (removing special characters not parsable by genfromtxt)
head = content[0]
head = head.replace('Protein FDR Confidence: Combined', 'Protein_FDR')
head = head.replace('Score Sequest HT: Sequest HT', 'Score_Sequest')
head = head.replace('# Peptides', 'Peptides')
head = head.replace('MW [kDa]', 'MW')
head = head.replace('# PSMs', 'PSMs')

#Determining number of abundance ratio values, removing original column names (contain non-parsable characters), appending a necessary number of ratio column names, and changing the delimiters to commas (for processing by genfromtxt)
abund_count = head.count("Abundance Ratio")
header = re.sub('Abundance Ratio \(log2\): \(F\d, Light\) / \(F\d, Heavy\)\s', '', head)
for i in range(abund_count):
    header = header + "Abundance" + str(i+1) + "\t"
header = header.replace("\t",", ")

columns_list = header.split(', ')
print(columns_list)
#Extracting columns of interest from the text file using genfromtxt (raising exceptions if any of the parameters are not present in the input file)
try:
    if "Accession" in columns_list:
        accession_data = np.genfromtxt(filename, skip_header=1, names=header, delimiter="\t", usecols=("Accession"), encoding=None, dtype=None)
    else:
        raise InputError("\nProtein accession numbers are not provided\n")
        quit()
    if "Description" in columns_list:
        description_data = np.genfromtxt(filename, skip_header=1, names=header, delimiter="\t", usecols=("Description"), encoding=None, dtype=None)
    else:
        raise InputError("\nProtein descriptions are not provided\n")
        quit()
    if "MW" in columns_list:
        mw_data = np.genfromtxt(filename, skip_header=1, names=header, delimiter="\t", usecols=("MW"), encoding=None, dtype=None)
    else:
        raise InputError("\nMolecular weights are not provided\n")
        quit()
    if "Peptides" in columns_list:
        peptide_data = np.genfromtxt(filename, skip_header=1, names=header, delimiter="\t", usecols=("Peptides"), encoding=None, dtype=None)
    else:
        raise InputError("\nNumbers of peptides are not provided\n")
        quit()
    if "PSMs" in columns_list:
        psm_data = np.genfromtxt(filename, skip_header=1, names=header, delimiter="\t", usecols=("PSMs"), encoding=None, dtype=None)
    else:
        raise InputError("\nNumbers of PSMs are not provided\n")
        quit()
    if "Abundance1" in columns_list:
        ratio_data = np.genfromtxt(filename, skip_header=1, names=header, delimiter="\t", usecols=("Abundance1", "Abundance2", "Abundance3", "Abundance4"), encoding=None, dtype=None)
    else:
        raise InputError("\nAbundance ratios are not provided\n")
        quit()
except:
    print("Could not parse the input file\n")
    quit()

#Calculating the median and number of valid values for each column
medians = []
lens = []
for i in range(len(ratio_data[0])):
    counter = 0
    arr = []
    for j in range(len(ratio_data)):
        if np.isnan(ratio_data[j][i]) == False:
            counter += 1
            arr.append(ratio_data[j][i])
    medians.append(stats.median(arr))
    lens.append(counter)

proteins = []

#Defining the Protein object which stores all the parameters related to a protein entry in the table
class Protein:
    #Constructor method
    def __init__(self, accession, description, mw, peptides, PSMs, ratios_raw):
        self.accession = accession.tolist()
        self.description = description.tolist()
        self.peptides = peptides.tolist()
        self.PSMs = PSMs.tolist()
        self.mw = mw.tolist()
        self.ratios_raw = ratios_raw
        self.ratios_corrected = ratios_raw
        self.raw_list = ratios_raw.tolist()

    #Counting the number of valid (not-nan) ratios provided to the object
    def N(self):
        n = 0
        for i in range(len(self.ratios_raw)):
            if np.isnan(self.ratios_raw[i]) == False:
                n += 1
        return n

    #Correcting each raw abundance ratio
    def correction(self):
        for i in range(len(self.ratios_raw)):
                if self.ratios_raw[i] == 6.64:
                    self.ratios_corrected[i] = 6.64
                elif self.ratios_raw[i] == -6.64:
                    self.ratios_corrected[i] = -6.64
                elif np.isnan(self.ratios_raw[i]):
                    self.ratios_corrected[i] = 'nan'
                elif self.ratios_raw[i] > 6.64:
                    self.ratios_corrected[i] = 6.64
                elif self.ratios_raw[i] < -6.64:
                    self.ratios_corrected[i] = -6.64
                else:
                    self.ratios_corrected[i] = self.ratios_raw[i] - medians[i]

    #Calculating the average of all valid ratios
    def avg(self):
        sum = 0
        n = self.N()
        for i in self.ratios_corrected:
            if np.isnan(i) == False:
                sum += i
        if n != 0 and np.isnan(n) == False:
            return sum / n
        else:
            return 0

    #Calculating the standard deviation of all valid ratios
    def std_dev(self):
        self.ratios_notnan = []
        for i in self.ratios_corrected:
            if np.isnan(i) == False:
                self.ratios_notnan.append(i)
        return np.std(self.ratios_notnan)

    #Calculating the standard error of all valid ratios
    def std_error(self):
        n = self.N()
        self.dev = self.std_dev()
        if n != 0 and np.isnan(n) == False:
            return (self.dev / math.sqrt(n))
        else:
            return 0

    #Printing all formatted parameters of a protein object
    def display(self):
        print('------------------------------\n')
        print('***** PROTEIN DATA *****\n')
        print('Accession number: {}\n'.format(self.accession[0]))
        print('Description: {}\n'.format(self.description[0]))
        print('Molecular weight: {}\n'.format(self.mw[0]))
        print('No. PSMs: {}\n'.format(self.PSMs[0]))
        print('No. peptides: {}\n'.format(self.peptides[0]))
        print('Raw light/heavy ratio values: {}\n'.format(self.raw_list))
        print('Corrected light/heavy ratio values: {}\n'.format(self.ratios_corrected))
        print('Average light/heavy ratio value: {}\n'.format(self.avg()))
        print('N-value: {}\n'.format(self.N()))
        print('Standard deviation: {}\n'.format(self.std_dev()))
        print('Standard error: {}\n'.format(self.std_error()))

    #Formatting all protein parameters as a single line to be writted to a file
    def strformat(self):
        self.round_raw = []
        self.round_corr = []
        #Rounding all ratios and appending them to the new lists of ratios
        for i in self.raw_list:
            self.round_raw.append(round(i, 2))
        self.corrected_list = self.ratios_corrected.tolist()
        for i in self.corrected_list:
            self.round_corr.append(round(i,2))
        #Concatenating the individual ratio strings and delimiting them with tabs
        self.str_rraw_concat = str(self.round_raw)
        self.str_rraw_concat = self.str_rraw_concat.replace(',','\t')
        self.str_rcorr_concat = str(self.round_corr) #RuntimeWarning: invalid value encountered in true_divide
        self.str_rcorr_concat = self.str_rcorr_concat.replace(',','\t')
        #Rounding the average, standard deviation, and standard error values if they are non-nan
        if np.isnan(self.avg()) == False:
            self.avg_val = str(round(self.avg(),2))
        else:
            self.avg_val = str(self.avg())
        if np.isnan(self.std_dev()) == False:
            self.std_dev_val = str(round(self.std_dev(),2))
        else:
            self.std_dev_val = str(self.std_dev())
        if np.isnan(self.std_error()) == False:
            self.std_error_val = str(round(self.std_error(),2))
        else:
            self.std_error_val = str(self.std_error())
        #Writing the protein parameters into a list, appending the raw/corrected ratio strings, joining into a single string, and removing redundant square brackets
        ls = [str(self.accession[0]), str(self.description[0]), str(round(self.mw[0],2)), str(self.PSMs[0]), str(self.peptides[0]), self.avg_val, self.std_dev_val, self.std_error_val]
        ls.append(self.str_rraw_concat)
        ls.append(self.str_rcorr_concat)
        string = "\t".join(ls)
        string = string.replace('[','')
        string = string.replace(']','')
        return string

#Obtaining the number of rows, iterating over each row, and creating new Protein() object for each/assigning all relevant parameters
num_rows = accession_data.size
for i in range(num_rows):
    accession = accession_data[i]
    description = description_data[i]
    mw = mw_data[i]
    peptides = peptide_data[i]
    PSMs = psm_data[i]
    ratios_raw = ratio_data[i]
    proteins.append(Protein(accession, description, mw, peptides, PSMs, ratios_raw)) #RuntimeWarning: invalid value encountered in double_scalars

#Iterating over each object and correcting its abundance ratios
for i in proteins:
    i.correction()
    #i.display()

#Printing interface info for the user
print("Reading data from file {} ...".format(filename)) #RuntimeWarning: Degrees of freedom <= 0 for slice
print("Median ratio values for raw data: {}".format(medians))
print("Number of valid repeats in each column: {}".format(lens))
print("Output data saved to {}".format(output_name))

#Formatting the header to be written to the output file
out_head = "Accession\tDescription\tMW [kDa]\t# PSMs\t# Peptides\tAverage\tStandard deviation\tStandard error\t"
for i in range(abund_count):
    new_str = "Abundance Ratio (raw, log2): (F" + str(i + 1) + ", Light) / (F" + str(i + 1) + ", Heavy)\t"
    out_head += new_str
for i in range(abund_count):
    new_str = "Abundance Ratio (corrected, log2): (F" + str(i + 1) + ", Light) / (F" + str(i + 1) + ", Heavy)\t"
    out_head += new_str

#Opening/creating the output file, writing in the header file, iterating over the proteins list, and writing in each line. Then closing the file.
handle = open(output_name, 'w')
handle.write(out_head)
handle.write("\n")
for i in proteins:
    handle.write(i.strformat())
    handle.write("\n")
handle.close()

#Print out median correction value?
#CLI tool
