############################################################################
#
# Supporting routines for UST Observatory data processing pipeline
#
############################################################################
import pdb, os, sys, datetime, time, pyfits, shutil, tempfile
from pyraf import iraf
from glob import glob
from pprint import pprint as pp

def BiasSubtract(images, cal_path, outbase="_b"):
#"""
# 	Locate and subtract a bias frame from a list of input images#
#
# PARAMETERS:
# 	images - list of images to process
#	cal_path - path to calibration data
#
# OPTIONAL PARAMETERS
#	outbase - string to append to the end of the filename
#
# RETURNS:
#	List of bias subtracted images
#"""
	
	# Get a list of bias frames for these images.
	bias_frames = [FindBiasFrame(i, cal_path) for i in images]	
		
	# Build the list of output image names
	out = [os.path.splitext(i) for i in images]	# Split off the extension
	out = [i[0] + outbase + '.fits' for i in out]	# Paste the outbase at the end of the filename 
												# and put the extension back on
	# run imarith to do the bias subraction	
	iraf.imarith.unlearn()
	iraf.imarith.op = '-'
	iraf.imarith.mode = 'h'

	print "\n******************"
	print "Bias Subtracting: "
	print "******************"
	for i in range(len(images)):
		iraf.imarith.operand1 = images[i]
		iraf.imarith.operand2 = bias_frames[i]
		iraf.imarith.result = out[i]

		print images[i] + " - " + bias_frames[i]
		iraf.imarith()

    # Make sure that imarith actually created the output files.
    # Filter out any output files that don't exist.
	out = filter(os.path.exists, out)
        
	return out

############################################################################
# NAME: DarkSubtract
#
# DESCRIPTION:
# 	Locate and subtract dark frames from a list of input images
#
# PARAMETERS:
# 	images - list of images to process
#	cal_path - path to calibration data
#
# OPTIONAL PARAMETERS
#	outbase - string to append to the end of the filename. Default = "_d"
#
# RETURNS:
#	List of dark subtracted images
#
############################################################################
def DarkSubtract(images, cal_path, outbase="_d"):
	
	# Get a list of dark images
	darks = [FindDarkFrame(i, cal_path) for i in images]
	out = [os.path.splitext(i)[0]+outbase+'.fits' for i in images]

	iraf.imarith.unlearn() # initial imarith setup
	iraf.imarith.mode='h'

	print "\n******************"
	print "Dark Subtracting: "
	print "******************"
	for i in range(len(images)):

		iexp_time = GetHeaderKeyword(images[i], 'exptime')
		dexp_time = GetHeaderKeyword(darks[i], 'exptime')

		# If exposure times don't match, scale the dark and fill in the operand2 field
		if iexp_time != dexp_time:
			iraf.imarith.operand1 = darks[i]
			iraf.imarith.operand2 = iexp_time/dexp_time	
			iraf.imarith.op = '*'

			# Create temporary dark filename
			tdark = os.path.join(os.path.dirname(darks[i]),'tmpdark')
			iraf.imarith.result = tdark
			iraf.imarith()
		
			iraf.imarith.operand2 = tdark

		else: 
			iraf.imarith.operand2 = darks[i]

		# Perform the dark subtraction
		iraf.imarith.operand1 = images[i]
		iraf.imarith.op = '-'
		iraf.imarith.result = out[i]
		print iraf.imarith.operand1 + ' - ' + iraf.imarith.operand2
		iraf.imarith()

		# Remove the scaled dark
		if iexp_time != dexp_time:
			os.remove(tdark+'.fits')

	# Make sure out files actually exist 
	out = filter(os.path.exists, out)
	
	return out
		
############################################################################
# NAME: FlatField
#
# DESCRIPTION:
# 	Apply a flat field to a list of images.
#
# PARAMETERS:
# 	images - list of images to process
#	cal_path - path to calibration data
#
# OPTIONAL PARAMETERS
#	outbase - string to append to the end of the filename. Default = "_f"
#
# RETURNS:
#	List of dark subtracted images
#
############################################################################
def FlatField(images, cal_path, outbase='_f'):
	
    

	# Get a list of flat frames
	flats = [FindFlatFrame(i, cal_path) for i in images]

	# Build the output list
	out = [os.path.splitext(i)[0]+outbase+'.fits' for i in images]
	
	Ret = []		# Empty list to hold return

	#setup imarith basics
	iraf.imarith.unlearn()
	iraf.imarith.op = '/'
	iraf.imarith.mode = 'h'

	print "\n******************"
	print "Flat Fielding: "
	print "******************"
	for i in range(len(images)):
		
		if flats[i] != "":
		
			iraf.imarith.operand1 = images[i]
			iraf.imarith.operand2 = flats[i]
			iraf.imarith.result = out[i]
			iraf.imarith()


			print images[i] + ' / ' + flats[i]			
			Ret.append(out[i])
		
		else:
			print "No flat found for " + images[i]

		
	return Ret
	

############################################################################
# NAME: FindBiasFrame
#
# DESCRIPTION:
# 	Locate a bias frame for an image based on the time stamp.  
#	Searches for a bias frame from the observing night indicated by the 'date-obs' keyword
# 	in the header.  If no bias frame for the observing night is found, takes the master
#	bias frame from the "Standard" directory.
#
# PARAMETERS:
# 	image - image to process
#	cal_path - Path to calibration data
#
# RETURNS:
#	The fully qualified path to a bias frame for this image
#
############################################################################
def FindBiasFrame(image, cal_path):

	# Get the observation date in a YYYMMDD string
	date = ObservationDateString(image)

	# If a bias frame from this observing night exists, it will be here
	bias_path = os.path.join(cal_path,date,'Bias',date+'mbias.fits')

	# The standard master bias frame should be here
	stand_bias_path = os.path.join(cal_path,'Standard','Bias','mbias.fits')
            
	# Look for a master bias frame from this observing night
	if os.path.exists(bias_path):
		return bias_path
	elif os.path.exists(stand_bias_path):
		return stand_bias_path
	else:
		print "No bias frame found."
		return ""

############################################################################
# NAME: FindDarkFrame
#
# DESCRIPTION:
# 	Locate a dark frame for an image based on the exposure time and time stamp.  
#	Locates dark frames in this order, preferring unscaled frames.
#		1. An unscaled dark from the current observing night.
#		2. An unsclaed dark from the Standard directory.
#		3. A scaled dark from the current observing night.
#		4. A scaled dark from the Standard directory.	
#	
# PARAMETERS:
# 	image - image to process
#	cal_path - Path to calibration data
#
# RETURNS:
#	The fully qualified path to a dark frame for this image
#	The null string if one cannot be found.
#
############################################################################
def FindDarkFrame(image, cal_path):

	# Get the observation date in a YYYMMDD string
	date = ObservationDateString(image)

	# Get the exposure time of this image for the unscaled darks
	exp_time = str(GetHeaderKeyword(image, 'exptime'))
	
	# Build the four paths to scaled and unscaled dark frames.
	unscaled_date_path = os.path.join(cal_path,date,'Dark',date+'mdark'+exp_time+'.fits')
	unscaled_standard_path = os.path.join(cal_path,'Standard','Dark','mdark'+exp_time+'.fits')
	scaled_date_path = os.path.join(cal_path,date,'Dark',date+'mdark.fits')
	scaled_standard_path = os.path.join(cal_path,'Standard','Dark','mdark.fits')

	# Search for an appropriate dark frame
	if os.path.exists(unscaled_date_path):
		return unscaled_date_path	
	elif os.path.exists(unscaled_standard_path):
		return unscaled_standard_path	
	elif os.path.exists(scaled_date_path):
		return scaled_date_path	
	elif os.path.exists(scaled_standard_path):
		return scaled_standard_path	
	else: 
		return ""
	
############################################################################
# NAME: FindFlatFrame
#
# DESCRIPTION:
# 	Locate a flat frame for an image based on filter and observation date
#	Locates flat frames in this order
#		1. Same filter from this observing night
#		2. An unsclaed dark from the Standard directory.
#	
# PARAMETERS:
# 	image - image to pair with flat frame
#	cal_path - Path to calibration data
#
# RETURNS:
#	The fully qualified path to a flat frame for this image
#	The null string if one cannot be found.
#
############################################################################
def FindFlatFrame(image, cal_path):
	
	date = ObservationDateString(image)			# Get the observation date for this image
	ifilter = GetHeaderKeyword(image,'filter')	# Get the filter

	# Build the paths
	date_path = os.path.join(cal_path,date,'Flat',ifilter,date+'mflat'+ifilter+'.fits')
	standard_path = os.path.join(cal_path,'Standard','Flat',ifilter,'mflat'+ifilter+'.fits')

	# Search for an appropriate dark frame
	if os.path.exists(date_path):
		return date_path	
	elif os.path.exists(standard_path):
		return standard_path	
	else: 
		return ""


############################################################################
# NAME: ExpNormalize
#
# DESCRIPTION:
# 	Normalize a list of input images to a one second exposure.
# 	Simply divides each image by its exposure time.
#	Updates the 'exptime' header keyword to '1'
#
# PARAMETERS:
# 	images - list of images to process
#	cal_path - path to calibration data
#
# OPTIONAL PARAMETERS
#	outbase - string to append to the end of the filename
#
# RETURNS:
#	List of bias subtracted images
#
############################################################################
def ExpNormalize(images, outbase="_n"):
			
	# Build the list of output image names
	out = [os.path.splitext(i) for i in images]	# Split off the extension
	out = [i[0] + outbase + '.fits' for i in out]	# Paste the outbase at the end of the filename 
												# and put the extension back on
	# Get a list of exposure times.
	exp_times = [GetHeaderKeyword(i, 'exptime') for i in images]
	exp_times = [str(e) for e in exp_times]	
	
	# run imarith to do the normalization
	iraf.imarith.unlearn()
	iraf.imarith.op = '/'
	iraf.imarith.mode = 'h'

	for i in range(len(images)):
		iraf.imarith.operand1 = images[i]
		iraf.imarith.operand2 = exp_times[i]
		iraf.imarith.result = out[i]
	
		iraf.imarith()

		# update the exptime keyword		
		iraf.hedit.unlearn()
		iraf.hedit.verify='no'
		iraf.hedit.show='yes'
		iraf.hedit.update='yes'
		iraf.hedit.images=out[i]
		iraf.hedit.fields='exptime'
		iraf.hedit.value=1
		iraf.hedit.mode='h'

		iraf.hedit(Stdout=1)

	return out


############################################################################
# NAME: ObservationDateString
#
# DESCRIPTION:
# 	Build the observation date string in YYYYMMDD format from the observation
#	date keyword in the fits header.
#
# PARAMETERS:
# 	image - image from which to extract observation date info.
#
# OPTIONAL PARAMETERS:
#	keyword - Observation date keyword.  default="date-obs"
#	hdu - The header data unit.  Default is 0 (first one).
#
# RETURNS:
#	The observation date in a string as YYYYMMDD
#	A null string if the keyword doesn't exist or the image can't be read
#
############################################################################
def ObservationDateString(image, keyword='date-obs', hdu=0):

	date = ""

	# Convert date into a datetime object
	obs_date = GetObsDateTime(image,keyword=keyword, hdu=hdu)

	# If the hour in the observation datetime string is less than twelve (the datetime string
	#   uses a 24-hour clock system), then the date of the observation in the datetime string
	#   refers to the observation night of the previous date.  (observation night changes at noon) 
	if obs_date.hour < 12:
		obs_date = obs_date - datetime.timedelta(days = 1)

	# Format the date to match the date directories (YYYYMMDD)
	date = obs_date.date().__format__('%Y%m%d')

	return date
	

############################################################################
# NAME: GetObsDateTime
#
# DESCRIPTION:
#	Return a python datetime object using the DATE-OBS keyword from the 
#	image header
#
# PARAMETERS:
# 	image - image from which to extract observation date info.
#
# OPTIONAL PARAMETERS:
#	keyword - Observation date keyword.  default="date-obs"
#	hdu - The header data unit.  Default is 0 (first one).
#
# RETURNS:
#	A datetime object created from the DATE-OBS header keyword.
#	
############################################################################
def GetObsDateTime(image, keyword='date-obs', hdu=0):
	return datetime.datetime.strptime(GetHeaderKeyword(image, 'date-obs'),'%Y-%m-%dT%H:%M:%S')

############################################################################
# NAME: GetHeaderKeyword
#
# DESCRIPTION:
# 	Extract the value of a fits header keyword. 
#
# PARAMETERS:
# 	image - image to extract header from
#	keyword - header keyword whose value is to be extracted
#
# OPTIONAL PARAMETERS:
#	hdu - The header data unit.  Default is 0 (first one).
#
# RETURNS:
#	The value in the header keyword on success.
#	A null string if the keyword doesn't exist or the image can't be read
#
############################################################################
def GetHeaderKeyword(image, keyword, hdu=0):
	
	try:
		hdulist = pyfits.open(image)			# Open the image
		value = hdulist[hdu].header[keyword]	# Extract the keyword
	except (IOError, KeyError), e:
		print "GetHeaderKeyword: "
		print e									# Send the error message to stdout
		value = ""								# Return null on error

	return value

############################################################################
# NAME: CleanAncillary
#
# DESCRIPTION:
# 	Remove a list of files (checks for existance first)
#
# PARAMETERS:
# 	files - the list of files to be removed
#
# RETURNS:
# 	No return value.
#
############################################################################
def CleanAncillary(files):

	# Loop the list
	for f in files:
		if os.path.exists(f):
			os.remove(f)


############################################################################
# NAME: fits_filter
#
# DESCRIPTION:
#	Determine if a file is a fits file or not based on the file extension
#	Intended for use with the python filter() function.
#
# PARAMETERS:
# 	filename - The file to be tested
#
# RETURNS:
#	True if the file extension is a standard fits extension
#	False if the file extension is not a standard fits extnension
#
############################################################################
def fits_filter(filename):

    extension = os.path.splitext(filename)[1]
    return extension == '.fits' or extension == '.fit' or extension == '.fts'

def ppl(l):
	for i in l:
		print i

############################################################################
# NAME: FixFilenames
#
# DESCRIPTION:
#	Replace spaces with underscores in a list of files
#
# PARAMETERS:
# 	files - The file to be renamed
#
# RETURNS:
#	The list of files with modifications to the filenames.
#	If no modification was made, the orgiginal filename is returned.
#
############################################################################
def FixFilenames(files):

	outf = list(files)

	for i in range(len(outf)):
		outf[i] = outf[i].replace(' ','_')
		print "Original: " + files[i] + " Replace: " + outf[i]
		if outf[i] != files[i]:
			os.rename(files[i], outf[i])

	return(outf)













