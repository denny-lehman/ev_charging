pwd
cd ACN-Data-Static-main
ls
echo unzipping office_01 directory
cd office_01
gunzip *.gz
cd ..

echo unzipping caltech directory
cd caltech
gunzip *.gz
cd ..

echo unzipping jpl directory
cd jpl
gunzip *.gz
cd ..

echo ending script
