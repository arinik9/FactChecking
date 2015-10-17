#!/usr/bin/python3

file_name = "chomage-zone-t1-2003-t2-2015.xls"
f = open(file_name, 'r')

for l in f.readlines():
	print(l)
