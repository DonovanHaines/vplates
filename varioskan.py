import csv
import pandas as pd
import re
import string

########################################################################################################################
# Define a 'verbosity print' function to print only if verbosity is higher or equal to level in print statement
def verbprint(level, message): 
    if verbosity>=level :
        print(message)

########################################################################################################################
def legit_value(string_to_test) :
    try:
        float(string_to_test)
        return True
    except :
        return False

########################################################################################################################
########################################################################################################################
########################################################################################################################

class PlateExp: # class for each experiment (part) in Varioskan run
    experiment_type = "uninitialized" # will read experiment type from file
    experiment_name = "uninitialized" # will read experiment type from file
    sample_list = []
    rowlist= []
    num_wells = 0   # number of wells per plate, should = num_rows * num_cols
    num_plates = 0  # number of plates
    num_rows = 0    # rows on each plate
    num_cols = 0    # cols on each plate
    num_samples = 0 # number of actual samples with data (<=num_wells*num_plates)
    fixed_excitation = 0
    fixed_emission = 0
    sample_names = []
    filename = "none"
    data=pd.DataFrame(columns=['plate','row','column', 'excitation', 'emission', 'value'])
    
########################################################################################################################
    def readcsv(self, filename):
        verbprint(20, "Reading csv file: " + filename)
        with open(filename) as csvDataFile :
            readCSV = csv.reader(csvDataFile, delimiter=',')
            verbprint(40, "CSV reader loaded.")
            recent_excite=0
            recent_emit=0
            self.num_plates=0
            self.num_cols=0
            self.num_rows=0
            recent_plate_num=0
            recent_plate_name="none"
            phase = 0 # will be 1 for sample, 2 for value plates
            regex_plate = re.compile(r'^Plate\s(\d{1,3}):(.*)\s-\sEx:\s(\d{1,4})\snm,\sEm:\s(\d{1,4})\snm') #regex expression for parsing lines with excite and emit
            regex_plate_p = re.compile(r'^Plate\s(\d{1,3}):(.*)\s-\sWavelength:\s(\d{1,4})\snm') #regex expression for parsing lines with photometric
            regex_plate_row = re.compile(r'^\s*[A-P]$') #accomodates up to 384 well plate
            for row_num,row in enumerate(readCSV):
                if (row_num<25) :  #if first 25 rows, lower verbosity requirement for printing so get a header
                    verbprint(45,"Processing row number " + str(row_num+1) + ".")
                    verbprint(60,row)
                    verbprint(65, "Length is " + str(len(row)))
                else:  #after that, only print at higher verbosity
                    verbprint(75,"Processing row number " + str(row_num+1) + ".")
                    verbprint(90,row)
                    verbprint(95, "Length is " + str(len(row)))
            
                if row_num==1 : #remember, row_num is 0 for the first row so this is the 2nd really
                    verbprint(10,"Run type is " + row[0]+".")
                    self.experiment_type = row[0]

                match=re.search(regex_plate, row[0])
                if match: #We have a line with plate number, name, excitation wavelength, and emission wavelength
                    verbprint(80, "New excite and emit:  "+row[0])
                    recent_plate_num=int(match.group(1))
                    recent_plate_name=match.group(2)
                    recent_excite=int(match.group(3))
                    recent_emit=int(match.group(4))
                    if recent_plate_num>self.num_plates:
                        self.num_plates=recent_plate_num
                matchp=re.search(regex_plate_p, row[0])
                if matchp: #We have a line with plate number, name, wavelength
                    verbprint(80, "New photometric wavelength:  "+row[0])
                    recent_plate_num=int(matchp.group(1))
                    recent_plate_name=matchp.group(2)
                    recent_excite=int(matchp.group(3))
                    recent_emit=0
                    if recent_plate_num>self.num_plates:
                        self.num_plates=recent_plate_num
                        
                if row[0] == "Sample": 
                    phase =1
                    for test_col in range(len(row)) :
                        if legit_value(row[test_col]):
                            self.num_cols=max(self.num_cols, int(row[test_col]))
                    #num_cols=max(int(row))
                if row[0] == "Value": 
                    phase=2
                    for test_col in range(len(row)) :
                        if legit_value(row[test_col]):
                            self.num_cols=max(self.num_cols, int(row[test_col]))
                    #num_cols=max(row)
                match2=re.search(regex_plate_row, row[0])
                if match2: # is a row of either sample names or of values because it starts with a single letter
                    verbprint(100, "Matches pattern to be a plate row, processing "+str(self.num_cols)+ " columns.")
                    if (1+ord(row[0].lstrip())-ord('A'))>self.num_rows:
                        self.num_rows=1+ord(row[0].lstrip())-ord('A')  # a higher row than we have processed yet, so increase num_rows
                    if phase == 1: #sample names
                        #TODO: Add sample name reading code here
                        verbprint(25, "Warning - sample name reading not added yet!")
                    if phase == 2: #values
                        verbprint(100, "Match in phase 2. Parsing values.")
                        for this_col in range(self.num_cols) :
                            verbprint(99, "Testing plate row "+str(row[0])+" col "+str(this_col+1)+" ex "+str(recent_excite)+" em " +str(recent_emit)+"   value: " + str(row[this_col+1]) + "       is numeric? "+str(legit_value(row[this_col+1])))
                            if legit_value(row[this_col+1]):
                                verbprint(90, "Adding plate row "+str(row[0])+" col "+str(this_col+1)+" ex "+str(recent_excite)+" em " +str(recent_emit)+"   value: " + str(row[this_col+1]) + "       is numeric? "+str(legit_value(row[this_col+1])))
                                self.data = self.data.append([{'plate':recent_plate_num,
                                    'row':row[0].lstrip(),
                                    'column': (this_col+1), 
                                    'excitation': recent_excite,
                                    'emission': recent_emit, 
                                    'value':float(row[this_col+1]) }])
        verbprint(50, "Leaving readcsv(). Object Number of Plates: " + str(self.num_plates) + "  Num. rows: "+str(self.num_rows)+"  Num. cols: "+str(self.num_cols))
        if self.data.loc[:,"emission"].median()==0:
            self.experiment_type="photometric"
            verbprint(25, "Data determined to be photometric.")
        elif self.data.loc[:,"emission"].std()>self.data.loc[:,"excitation"].std() :
            self.experiment_type="emission"
            verbprint(25, "Data determined to be emission.")
        else: 
            self.experiment_type="excitation"
            verbprint(25, "Data determined to be excitation as it wasn't photometric or emission.")
        
        #Now to update some variables used by other functions later to save time
        self.rowlist=self.rowletterlist(self.num_rows) #generate list of letters for rows to index later
        self.update_sample_table()
        self.num_samples=len(self.sample_list)
        
        #now to add a column with the sample names
        def create_name(row):
            return str(row['plate'])+":"+str(row['row'])+str(row['column'])
        self.data["sample_name"]=self.data.apply(create_name, axis=1)
        self.data=self.data.reindex_axis(['sample_name', 'plate', 'row', 'column', 'excitation', 'emission', 'value'], axis=1)
        
########################################################################################################################
    def plotall(self): 
        import matplotlib.pyplot as plt
        import numpy as np
        #self.rowlist=self.rowletterlist(self.num_rows) #generate list of letters for rows to index later
        verbprint(50, "Entering plotall(). Number of Plates: " + str(self.num_plates) + "  Num. cols: "+str(self.num_cols) + "  Num. rows: "+str(self.num_rows)+".    Exp type: "+str(self.experiment_type)+".")
        fig = plt.figure() #create a blank page
        ax=fig.add_subplot(1,1,1) #create a blank plot that fills that fills the page
        if self.experiment_type=="emission":  #TODO: Right now ignores excitation wavelength(s), can expand later
            plt.xlabel("Excitation Wavelength (nm)")
            plt.ylabel("Fluorescence (counts) (Ex "+"{:.0f}".format(self.data.loc[:,"excitation"].median())+" nm)")
            fig.suptitle("Varioskan Emission Spectra")
            for plate_counter in range (self.num_plates):
                for row_counter in range (self.num_rows):
                    for col_counter in range(self.num_cols):
                        verbprint(100, str(plate_counter)+","+str(row_counter)+","+str(col_counter)+" in plotall.")
                        verbprint(100, str(sum(ThisExp.data.plate.isin({plate_counter+1})))+","+str(sum(ThisExp.data.row.isin({self.rowlist[row_counter]})))+","+str(sum(ThisExp.data.column.isin({col_counter+1})))+ "  =and=  "+str(len(ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].emission)))
                        if len(ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].emission) > 0 :
                            ax.plot(ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].emission, ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].value, label=str(plate_counter+1)+":"+self.rowlist[row_counter]+str(col_counter+1))
        else:
            if self.experiment_type=="excitation":
                plt.xlabel("Excitation Wavelength (nm)")
                plt.ylabel("Fluorescence (counts) (Em "+"{:.0f}".format(self.data.loc[:,"emission"].median())+" nm)")
                fig.suptitle("Varioskan Excitation Spectra")
            elif self.experiment_type=="photometric":
                plt.xlabel("Wavelength (nm)")
                plt.ylabel("Absorbance")
                fig.suptitle("Varioskan Absorption Spectra")
            else:
                plt.xlabel("Wavelength (nM)")
                plt.ylabel("Signal")
                fig.suptitle("Varioskan Spectra")
            for plate_counter in range (self.num_plates):
                for row_counter in range (self.num_rows):
                    for col_counter in range(self.num_cols):
                        verbprint(100, str(plate_counter)+","+str(row_counter)+","+str(col_counter)+" in plotall.")
                        verbprint(100, str(sum(ThisExp.data.plate.isin({plate_counter+1})))+","+str(sum(ThisExp.data.row.isin({self.rowlist[row_counter]})))+","+str(sum(ThisExp.data.column.isin({col_counter+1}))))
                        if len(ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].excitation) > 0 :
                            ax.plot(ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].excitation, ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].value, label=str(plate_counter+1)+":"+self.rowlist[row_counter]+str(col_counter+1))                
        leg=ax.legend();
        return fig
        
########################################################################################################################
    def rowletterlist(self, number) : 
        result=list()
        if number>0 & number<27:
            for count in range(number):
                result.append(chr(ord("A")+count))
        return(result)
        
########################################################################################################################
    def update_sample_table(self):
        self.sample_list=[]
        for plate_counter in range (self.num_plates):
                for row_counter in range (self.num_rows):
                    for col_counter in range(self.num_cols):
                        verbprint(100, str(plate_counter)+","+str(row_counter)+","+str(col_counter)+" in update_sample_table.")
                        verbprint(100, str(sum(ThisExp.data.plate.isin({plate_counter+1})))+","+str(sum(ThisExp.data.row.isin({self.rowlist[row_counter]})))+","+str(sum(ThisExp.data.column.isin({col_counter+1}))))
                        if len(ThisExp.data[ThisExp.data.plate.isin({plate_counter+1})&ThisExp.data.row.isin({self.rowlist[row_counter]})&ThisExp.data.column.isin({col_counter+1})].excitation) > 0 :    
                            self.sample_list.append(str(plate_counter+1)+":"+self.rowlist[row_counter]+str(col_counter+1))

########################################################################################################################
    def ordered_csv(self,savefilename):                            
        newdf=self.ordered_data()
        newdf.to_csv(savefilename)
            
        
########################################################################################################################
    def ordered_data(self):                            
        if (self.experiment_type=="photometric") or (self.experiment_type=="excitation") :
            return self.data.pivot(index='excitation', columns='sample_name', values='value')
        elif (self.experiment_type=="emission"):
            return self.data.pivot(index='emission', columns='sample_name', values='value')
        else: 
            return self.data  #TODO: check other exp types and accomodate
            
        
                
########################################################################################################################
    def name_row(self,sample_list_name):   #work backwards to row from sample_list name                           
        regex_sample_name = re.compile(r'^(\d{1,5}):([A-P])(\d{1,5})$') #accomodates up to 384 well plate        
        match=re.search(regex_sample_name, sample_list_name)
        if match: #We have a legit sample name
            return match.group(2)
            
########################################################################################################################
    def name_column(self,sample_list_name):   #work backwards to column from sample_list name                           
        regex_sample_name = re.compile(r'^(\d{1,5}):([A-P])(\d{1,5})$') #accomodates up to 384 well plate        
        match=re.search(regex_sample_name, sample_list_name)
        if match: #We have a legit sample name
            return match.group(3)

########################################################################################################################
    def name_plate(self,sample_list_name):   #work backwards to plate from sample_list name                           
        regex_sample_name = re.compile(r'^(\d{1,5}):([A-P])(\d{1,5})$') #accomodates up to 384 well plate        
        match=re.search(regex_sample_name, sample_list_name)
        if match: #We have a legit sample name
            return match.group(1)      
########################################################################################################################
########################################################################################################################
########################################################################################################################

class PlateExpCollection :
    PlateExp = []  # list of Plate Experiments
    
    
#####################################################################################################################################    
#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################


# START MAIN SCRIPT
        
#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################
        
#parse the command line arguments
import argparse


parser = argparse.ArgumentParser(description='Read varioskan exported data. You should export report to excel and save a page as csv. This will load it and analyze.')
parser.add_argument('csvfile', help="The name of the exported csv file; exported as excel, then given tab (exp) exported as csv.")
parser.add_argument('--verbosity', type=int, default=10, dest='verbosity', 
help="Verbosity level: 0=quiet, 10 = verbose, 100 = max debug info.")

args=parser.parse_args()
verbosity=args.verbosity
verbprint(1,"Filename: " + args.csvfile + ".")
ThisExp = PlateExp()
ThisExp.readcsv(args.csvfile)
print(ThisExp.data)
verbprint(50, "Number of Plates: " + str(ThisExp.num_plates) + "  Num. rows: "+str(ThisExp.num_rows)+"  Num. cols: "+str(ThisExp.num_cols))

ThisExp.data.to_csv("output.csv")

import matplotlib.pyplot as plt
import numpy as np


myfig=ThisExp.plotall()
plt.show()

from pathlib import Path
save_filename=str(Path(args.csvfile).with_suffix(''))+" ordered.csv"

print(ThisExp.ordered_csv(save_filename))