'''Reverse Geocode Qualtrics

This script will reverse geocode US Qualtrics survey data by adding state and county.
Data should be in the CSV format exported form Qualtrics, with long/lat columns.
The first row should have headers. If there are multiple lines of headers, the 
option --mergeheaders may make sense of it. This requires the reverse_geocoder module.
'''

import sys
import reverse_geocoder
import argparse
import csv

def findSimilarHeader(headers, colName):
    '''Return first header similar to colName'''
    for idx,v in enumerate(headers):
        if v.lower().find(colName.lower()) >= 0:
            return idx

def mergeHeaders(headers, reader):
    '''Merge multiple headers lines

    In the case where there are multiple header lines, it should look like this:
        1. Header with survey question columns named like Q1, Q2
        2. Header with the same columns names, except survey questions are named with the full text.
        3. Header with JSON metadata for each column.
    '''
    headers2 = next(reader)
    if len(headers) != len(headers2):
        print('Headers 1 and 2 are not the same length.')
        sys.exit(1)

    # For each column name header 1 and 2, merge together if they are different
    for i in range(len(headers)):
        if headers[i] != headers2[i]:
            print(f'Merge headers "{headers[i]}" and "{headers2[i]}"')
            headers[i] = ' '.join((headers[i], headers2[i]))

    # Ignore the metadata header
    next(reader)

def main(reader, writer, mergeheaders, colLat, colLong):
    # We require headers on first row.
    headers = next(reader)
    if mergeheaders:
        mergeHeaders(headers, reader)
    print("Found headers", headers)

    if not colLat:
        colLat = findSimilarHeader(headers, 'latitude')
    if not colLong:
        colLong = findSimilarHeader(headers, 'longitude')
    if not colLat or not colLong:
        print("Couldn't find latitude or longitude column.")
        sys.exit(1)
    print(f'Using column {colLat}: {headers[colLat]} for latitude.')
    print(f'Using column {colLong}: {headers[colLong]} for longitude.')

    headers.append('state')
    headers.append('county')
    writer.writerow(headers)

    rowCount = 0
    for idx,row in enumerate(reader):
        latitude = row[colLat]
        longitude = row[colLong]

        state = None
        county = None
        if latitude and longitude:
            # Not optimized
	        geodata = reverse_geocoder.search((latitude, longitude))
	        state = geodata[0]['admin1']
	        county = geodata[0]['admin2']
        else:
        	print("Missing coordinates for row", idx)

        row.append(state)
        row.append(county)
        writer.writerow(row)
        # if rowCount >= 50:
        #    break
        rowCount += 1

    print(f'Processed {rowCount} rows.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputfile', help='CSV input file')
    parser.add_argument('outputfile', help='CSV output file')
    parser.add_argument('-mh','--mergeheaders', default=True, help='Merge and clean multiple headers from qualtrics.')
    parser.add_argument('-lt','--latitude', type=int, help='Column number for latitude, 0-indexed. Otherwise look for column with header like "latitude."')
    parser.add_argument('-lg','--longitude', type=int, help='Column number for longitude, 0-indexed. Otherwise look for column with header like "longitude."')

    args = parser.parse_args()
    with open(args.inputfile, encoding='utf-8') as inputfile:
        with open(args.outputfile, 'w', encoding='utf-8') as outputfile:
            main(csv.reader(inputfile), csv.writer(outputfile), args.mergeheaders, args.latitude, args.longitude)


# workbook.save(filename="unvax-geocoded.xlsx")