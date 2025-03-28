% For decoding AIS data, see https://www.itu.int/rec/R-REC-M.1371/en,
% specifically Table 48 on page 109.
% For AIS Vessel Type, see https://coast.noaa.gov/data/marinecadastre/ais/VesselTypeCodes2018.pdf .

status(Ship, 'under way using engine') :- status(Ship, 0).
status(Ship, 'at anchor') :- status(Ship, 1).
status(Ship, 'not under command') :- status(Ship, 2).
status(Ship, 'restricted maneuverability') :- status(Ship, 3).
status(Ship, 'constrained by her draught') :- status(Ship, 4).
status(Ship, 'moored') :- status(Ship, 5).
status(Ship, 'aground') :- status(Ship, 6).
status(Ship, 'engaged in fishing') :- status(Ship, 7).
status(Ship, 'under way sailing') :- status(Ship, 8).
status(Ship, 'reserved for dangerous vessels') :- status(Ship, 9); status(Ship, 10).
status(Ship, 'power-driven vessel towing astern') :- status(Ship, 11).
status(Ship, 'power-driven vessel pushing ahead or towing alongside') :- status(Ship, 12).
status(Ship, 'power-driven vessel connected') :- status(Ship, 'power-driven vessel towing astern'); status(Ship, 'power-driven vessel pushing ahead or towing alongside').
status(Ship, 'special') :- status(Ship, 13); status(Ship, 14); status(Ship, 15).

% similar to status, but for the AIS Vessel Type (see Table 53 on page 114)
type(Ship, 'not available') :- type(Ship, 0).
% ... this is complicated

% The cargo type seems to redundant with type
