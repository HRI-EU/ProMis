% Imports
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:- use_module(library(db)). % for csv_load

% Ship data loading
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% For the specific format, see: https://coast.noaa.gov/data/marinecadastre/ais/faq.pdf .
:- csv_load('mini_data.csv', 'ais_report').

% For some attributes, we have to do some parsing. This will be done in a separate file.
% For others, we do not trust the data, so we will use distributions to model them
% and use `*_reported` for the AIS data.

ship(Ship) :- ais_report(Ship, _, _, _, _, _, _, _, _, _, _, _, _, _).
time(Ship, X) :- ais_report(Ship, X, _, _, _, _, _, _, _, _, _, _, _, _).
0.95:: sog_reported(Ship, X) :- ais_report(Ship, _, _, _, X, _, _, _, _, _, _, _, _, _).
0.99:: type(Ship, X) :- ais_report(Ship, _, _, _, _, _, _, X, _, _, _, _, _, _).
0.95:: status(Ship, X) :- ais_report(Ship, _, _, _, _, _, _, _, X, _, _, _, _, _).
% ... this is incomplete

% Ship data interpreatation
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:- consult('prolog_lib/ais_parsing.pl').

% we trust some data only somewhat. We could also make this a parameter to a distribution
% sog(Ship, X) ~ normal(X, 0.1), reported_sog(Ship, X).

% Weather information
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
wind_speed ~ normal(25, 5).
wind_direction ~ uniform(0, 360).

% The actual model
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

% proclaimed_depth(waterway_1) :- 6.
% depth(waterway) ~
%     wind_speed < 30,
%     normal(proclaimed_depth(waterway_1), 0.1)
%     ;
%     wind_speed >= 30,
%     normal(proclaimed_depth(waterway_1), 0.4) .

% % how to model that this is missing? some prior based on the ship type?
% announced_draft(vessel_1) ~ normal(3, 0.001).  % this is from a measurement
% announced_draft(vessel_1) ~ normal(3, 5). % without depth, we use a prior (-> learn this from data)
% ...
% draft(vessel_1) ~
%     normal(announced_draft(vessel_1), 0.75).

% 0.9::anchoring(vessel_1).
% ...
% in_movement(vessel_1) :- \+anchoring(vessel_1).

% % emergency vessels have different behaviour

% % Example statements
% will_follow_waterway(vessel, waterway) :-
%     depth(waterway_1) >= draft(vessel_1) + 0.5,
%     distance(vessel, other_vessel) > 100,
%     abs(heading(vessel) - alignment(waterway)) < 10,
%     (
%         is_following(vessel, waterway),
%         ;
%         \+is_following(vessel, waterway),
%         in_movement(vessel_1)
%     ) .

% % in the end, we need:
% action(vessel_1, ?).
% % -> could be follow waterway 1, follow waterway 2,
% % anchor, change course, dock

% Queries
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
query(status(ship_367121040, 'at anchor')).

% ####

% # model this as independent for fast and simple inference
% anchoring(Ship, Lat, Lon) :- is_legal, makes_sense, is_safe.
% follow_lane :- is_legal, makes_sense, is_safe.
% ...

% # query the entire landscape at one time point, make path search over the entire landscape,
% # assuming it is static for the time being
% query(anchoring(ship_367121040, -, -)).
