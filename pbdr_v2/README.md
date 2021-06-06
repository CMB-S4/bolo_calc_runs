
### Things changes from pbdr_v1:

- SAT LF and UHF bands now same as LAT.
- LAT UHF wafer layout, detector count, horn size now same as SAT.
- CHLAT new baseline elevation is 40 deg, not 35deg.

Notes:  
- carrier_index = beta = 2.7 as default.  This is (approximately) the highest of the fab-reported values.
- Psat_factor = 3.0 for LATs, 2.5 for SATs.

Psats from Basemodel runs using all nominal inputs:

CHLAT:  <br>
  Chan = ['LF_1','LF_2','MF_1','MF_2','UHF_1','UHF_2']        <br>
  Psat1 = [0.6856, 3.6253, 4.1380, 12.8813, 37.5136, 55.2783]   <br>

SPLAT:  <br>
  Chan = ['ULF_1, 'LF_1','LF_2','MF_1','MF_2','UHF_1','UHF_2'] <br>
  Psat2 = [0.4061, 0.6868, 4.3047, 4.6640, 11.5170, 29.1024, 39.9944]
  
SAT: <br>
  Chan = ['LF_1','LF_2','MF1_1','MF1_2','MF2_1','MF2_2', 'UHF_1','UHF_2'] <br>
  Psat3 = [1.4066, 6.3078, 7.3851, 12.2077, 7.6559, 13.2925, 29.8963, 39.0787]
  

LAT Psats, taking the average of CHLAT and SPLAT and rounding to 3 sig figs. <br>
Note that ULF is only in SPLAT. <br> 
  Chan = ['ULF_1, 'LF_1','LF_2','MF_1','MF_2','UHF_1','UHF_2'] <br>
  Psat = [ 0.406, 0.686, 3.97,  4.40 , 12.2 ,  33.3 , 47.6]
  
SAT Psats, making 90's be the average of MF1_1 and MF2_1, and the 150's be the average of MF1_2 and MF2_2, and rounding all to 3 sig figs. <br>
  Chan = ['LF_1','LF_2','MF1_1','MF1_2','MF2_1','MF2_2', 'UHF_1','UHF_2'] <br>
  Psat = [1.41, 6.31, 7.52, 12.8, 7.52, 12.8, 29.9, 39.1]
  
  
  
 
