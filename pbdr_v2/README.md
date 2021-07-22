
## Things changes from pbdr_v1:

- SAT LF and UHF bands now same as LAT.
- LAT UHF wafer layout, detector count, horn size now same as SAT.
- CHLAT new baseline elevation is 40 deg, not 35deg.
- SAT LF and MF lenses are HDPE (not alumina)
- Nylon filter (4K) added to LATR.
- Updated dielectric loss properties (see "inputs" section below);  same for mirror loss.

Notes:  
- carrier_index = beta = 2.7 as default.  This is (approximately) the highest of the fab-reported values.
- Psat_factor = 3.0 for LATs, 2.5 for SATs.

Psats are set by running SetFixedPsats.ipynb .  CHLAT and SPLAT Psat values are set to the average of the calculated values using psat_factor = 3.0.  SAT values for the LF and MF bands are set using psat_factor = 2.5, but the MF bands are set to the average of the calculated value for the higher and lower split bands.  ie, the MF1_1 and MF2_1 bands are set equal to the average of the two.

These fixed Psats are stored in the FixedPsats.toml file for later use by various notebooks.

## How to use this archive:

- Run SetFixedPsats.ipynb
- Run RunDefaultConfig.ipynb to get all the default values of everything.
- Run variation notebooks as desired.

## bolo-calc inputs:
See InputsNotes.ipynb
