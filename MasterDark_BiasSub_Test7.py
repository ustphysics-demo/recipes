# Emma Western June 24, 2014 Version 1.0
# Create a master dark fits file from images that have the same exposure time and print the
# number of outliers to the screen
##########

import os
from astropy.io import fits
import numpy as np

#################       UPDATE PATH AND FILENAME AND EXPOSURE TIME        #################3

##########
# DESCRIPTION
#   declares a path and calls all the functions
# PARAMETERS
#   path - where you want your files to come from
#   path2 - where you want to create the master dark
#   filename - what you want the master dark to be called
#   allFiles - all the files in the path
#   allFits - all the fits files in the path
#   images - all the fits files with the desired exposure time in the path
#   mean - the mean of all the images' data
# RETURNS
#   nothing
##########

def main():
    path = '/raid/data/home/observatory/software/Scripts/Emmas_Scripts/Fits_files/DarksMinusBias_Test7'
    path2 = '/raid/data/home/observatory/software/Scripts/Emmas_Scripts/Fits_files'
    filename = 'MasterDark_180s_Test7_Dark-Bias.fit'
    
    allFiles = os.listdir(path)
    allFits = sort(allFiles)
    images = onlySixHundred(allFits, path)
    
    mean = getmean(images, path)
    outliers(mean) 
    master_dark(mean, path2, filename)
    
    
    
##########
# Description
#	sorts the files in path
# Parameters
#	allFiles - list of files in path
#	allFits - list of fits files in path
#   name - name of file
#	ext - extension of the file
# Return
#	list of fits images
##########
	
def sort(allFiles):
    allFits = []
    for i in allFiles:
        [name, ext] = os.path.splitext(i)
        if ext == '.fits' or ext == '.fit' or ext == '.fts':
            allFits.append(i)		
    return allFits	
    
    
    
##########
# DESCRIPTION
#   makes a list of all the fits files that have the desired exposure time from the path
# PARAMETERS
#   allFits - list of all the fits files in the path
#   path - where the program looked to find the fits files
#   images - list of fits files with a certain exposure time
#   x - combines the path and image name so the program can open the file
#   hdulist - opens a fits file
#   head - header of a fits file
#   exp - the exposure time of a fits file
# RETURN
#   list of fits files with a certain exposure time
##########
    
def onlySixHundred(allFits, path):
    images = []
    
    for i in allFits:
        x = os.path.join(path, i)
        hdulist = fits.open(x)
        head = hdulist[0].header
        exp = head ['EXPOSURE']
        
        if exp == 180.0:
            images.append(i)

        hdulist.close()
    return images

    
    
##########
# DESCRIPTION
#   Finds the mean for the fits files
# PARAMETERS
#   images - list of fits files with certain exposure time
#   path - where the program looked to find the files
#   info - list of data from fits files
#   x - combines file name and path so the file can be opened
#   hdulist - opens a fits file
#   data - data of a fits file
#   dimensions - dimensions of fits file data
#   sum - the sum of all the data
#   n - how many images there are
#   mean - the mean of the fits files
# RETURN
#   mean
##########    
    
def getmean(images, path):
    
    # just to find the dimensions to create sum
    hdulist = fits.open(os.path.join(path, images[0]))
    data = hdulist[0].data
    hdulist.close()
    
    dimensions = data.shape
    sum = np.zeros(dimensions)
    
    for i in images:
        x = os.path.join(path, i)
        hdulist = fits.open(x)
        data = hdulist[0].data
        sum = sum + data
        hdulist.close()
        
    n = len(images)
    mean = sum / n

    return mean    
    
    
    
##########
# DESCRIPTION
#   find how many outliers there are based a threshold and print them
# PARAMETERS
#   mean - mean data from the fits images
#   num - number of outliers
# RETURN
#   nothing
##########
    
def outliers(mean):
    num = 0
    
    for i in range(len(mean)):
        for j in range(len(mean[i])):
            if mean[i][j] >= 10000:
                num = num + 1

    print num


    
##########
# DESCRIPTION
#   creates a new fits file from the mean data
# PARAMETERS
#   mean - mean data from the images
#   path2 - where you want the new fits to be created
#   filename - what you want the new filename to be called
#   hdu - puts the mean data into a fits format
#   newimage - combines path2 and filename
# RETURN
#   nothing
##########
    
def master_dark(mean, path2, filename):

    hdu = fits.PrimaryHDU(mean)
    newimage = os.path.join(path2, filename)
    
    if os.path.exists(newimage):
        os.remove(newimage)
        
    hdu.writeto(newimage)

   
if __name__ == "__main__": main()