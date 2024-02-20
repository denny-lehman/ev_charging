pwd
cd ACN-Data-Static-main
ls
echo unzipping office_01 directory
cd office_01
gunzip *.gz
cd ..

echo unzipping caltech directory
cd caltech
cd California_Garage_01
gunzip *.gz
cd ..
cd California_Garage_02
gunzip *.gz
cd ..
cd LIGO_01/
gunzip *.gz
cd ..
cd S_Wilson_Garage_01
echo $pwd
gunzip *.gz
cd ..
cd N_Wilson_Garage_01
gunzip *.gz
cd ..

cd ..


echo unzipping jpl directory
cd jpl
gunzip *.gz
cd ..

echo ending script
