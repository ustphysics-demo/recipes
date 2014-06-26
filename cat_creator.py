# -*- coding: utf-8 -*-
"""
Spyder Editor

This temporary script file is located here:
C:\Users\Maria\.spyder2\.temp.py
"""

from astropy.io import fits
import os

##########
# DESCRIPTION
#	Starts at base_path and it will call functions that create a text catalog.
# PARAMETERS
#	base_path - where you want the program to start running
#	images - the fits files in the current path
#	list - calls the function that will write the text file
# RETURNS
#	nothing
##########

def main():
    base_path = 'C:\Users\Maria\.spyder2\mar30_14'
    os.chdir(base_path)
    print os.getcwd()
    files = os.listdir(base_path)    
    images = sort(files)
    file(images)
            
            
##########
# DESCRIPTION
#	Sorts the images in the current folder so that you're left with fits files only
# PARAMETERS
#	images - list of fits files in the current working directory
# RETURNS
#	images
##########

def sort(files):
    images = []
    for i in files:
        [name, ext] = os.path.splitext(i)
        if ext == '.fits' or ext == '.fit' or ext == '.fts':
            images.append(i)		
    return images	

##########
# DESCRIPTION
#	Creates and writes into a file called catalog. It puts the iformation into
#     the text file.
# PARAMETERS
#	images - list of fits image names
#	filter - list of objects observed
#	exp    - list of exposure times
#	time   - list of times when the images were taken
#     air    - list of air mass
#     foc    - list of focuses
#     filenum- list of filenumbers 
# RETURNS
#	nothing
##########

def file(images):
    filenum = filenum_build(images)
    filter = color_build(images)
    exp = exp_List_build(images)
    air = Airmass_build(images)
    foc = Focus_build(images)    
    time = date_build(images)
    # creates a new catalog and puts into the variable info
    info = open("Prettycatalog.txt", "w")
    # writes information to file
    info.write("Filenumber,       Integ. Time,      AirMass,     Focus,   Time Taken,               Object and Filter,     Comments\n")
    # wirtes information from lists into files
    for i in range(len(images)):
        info.write('%s,\t\t' % filenum[i])
        info.write('\t%f,  ' % exp[i])        
        info.write('\t\t%s,' % air[i])        
        info.write('\t\t%s,' % foc[i])
        info.write('\t%s,' % time[i])
        info.write('\t%s,' % filter[i])         
        info.write('\n')

    info.close()
    
##########
# DISCRIPTION
#   builds a list called filnum that contains filenumbers
# PARAMETERS
#   filnum - list of filenumbers from filename()
# RETURNS
#   filnum - retruns list to file()
##########
def filenum_build(images):
    filnum = []
    for i in images:
	    filnum.append(filename(i))
    return filnum    

##########
# DISCRIPTION
#   loops through the filename and picks out the 4 character filenumber
# PARAMETERS
#   f - constructs the filenumber
# RETURNS
#   f - returns the filenumber back to filenum_build
##########
def filename(x):
    for i in x:
       f =""
       for j in range(len(x)):
           if j > 5 and j <10:
               f = f + x[j]
    return f
            
"""def extract(x):
    f =""
    for i in range(len(x)):
        if i > 5 and i <10:
            f = f + x[i]
    return f"""
    

##########
# DESCRIPTION
#	Takes each image and adds exp_Time's return value to the list exp.
# PARAMETERS	
#	images - list of fits files
#	exp - a list of exposure times
# RETURNS
#	list of exposure times
##########
def exp_List_build(images):
    exp = []
    for i in images:
        exp.append(exp_Time(i))
    return exp

##########
# DESCRIPTION
#	Opens a fits header, takes the exposure time and returns it.
# PARAMETERS
#	x - input file
#	hdulist - image information
#	head - the header
#	t - the exposure time
# RETURN
#	exposure time
##########		
def exp_Time(x):
    hdulist = fits.open(x)
    head = hdulist[0].header
    t = head ['EXPTIME']
    hdulist.close()
    return t 


##########
# DESCRIPTION
#	Takes each image and adds date_Time's return value to the list time.
# PARAMETERS	
#	images - list of fits files
#	time - a list of times when the images were taken
# RETURNS
#	list of times/dates
##########    
def date_build(images):
    time = []
    for i in images:
        time.append(date_Time(i))
    return time


##########
# DESCRIPTION
#	Opens a fits header, takes the time the image was taken and returns it.
# PARAMETERS
#	x - input file
#	hdulist - opens the image information
#	head - the header
#	d - the time when the image was taken
# RETURN
#	time an image was taken
##########
def date_Time(x):
    hdulist = fits.open(x)
    head = hdulist[0].header
    d = head ['DATE-OBS']
    hdulist.close()
    return d	


##########
# DESCRIPTION
#	Takes each image and adds color's return value to the list filter.
# PARAMETERS	
#	images - list of fits files
#	filter - a list of objects observed
# RETURNS
#	filter
##########
def color_build(images):
    filter = []
    for i in images:
	    filter.append(color(i))
    return filter
		

##########
# DESCRIPTION
#	Opens a fits header, takes the object and returns it.
# PARAMETERS
#	x - input file
#	hdulist - image information
#	head - the header
#	f - the object
# RETURN
#	object observed and through what filter if there was one
##########
def color(x):
    hdulist = fits.open(x)
    head = hdulist[0].header	
    f = head ['OBJECT']
    hdulist.close()
    return f
    

##########
# DISCRIPTION
#   builds a list called foc that contains the focus string from the header
# PARAMETERS
#   foc - list of focus strings
# RETURNS
#   foc - retruns list to file()
##########
def Focus_build(images):
    foc = []
    for i in images:
        foc.append(focus(i))
    return foc

##########
# DESCRIPTION
#	Opens a fits header, takes the focus and returns it.
# PARAMETERS
#	x - input file
#	hdulist - image information
#	head - the header
#	fo - the focus
# RETURN
#	fo - the focus returns to focus_build()
##########		
def focus(x):
    hdulist = fits.open(x)
    head = hdulist[0].header
    fo = head ['FOCUS']
    hdulist.close()
    return fo
    
    
##########
# DISCRIPTION
#   builds a list called air that contains the airmass string from the header
# PARAMETERS
#   air - list of air mass strings 
# RETURNS
#   air - retruns list to file()
##########
def Airmass_build(images):
    air = []
    for i in images:
        air.append(airmass(i))
    return air

##########
# DESCRIPTION
#	Opens a fits header, takes the airmass and returns it.
# PARAMETERS
#	x - input file
#	hdulist - image information
#	head - the header
#	a - the airmass
# RETURN
#	a - returns the airmass to Airmass_build()
##########
def airmass(x):
    hdulist = fits.open(x)
    head = hdulist[0].header
    a = head ['AIRMASS']
    hdulist.close()
    return a 
	  
    
if __name__=='__main__': main() 