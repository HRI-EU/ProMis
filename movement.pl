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
draft(Ship, d) :- ais_report(Ship, _, _, _, _, _, _, _, _, _, _, d, _, _).  % in reality, this is uncertain
% ... this is incomplete

% Ship data interpreatation
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:- consult('prolog_lib/ais_parsing.pl').

% we trust some data only somewhat. We could also make this a parameter to a distribution
% sog(Ship) ~ normal(X, 0.1), reported_sog(Ship, X).

% Weather information
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Comment: The Weibull is appropriate as a prior distribution for wind speed.
% However, we do have some observation with some uncertainty.
% https://www.reuk.co.uk/wordpress/wind/wind-speed-distribution-weibull
% https://en.wikipedia.org/wiki/Weibull_distribution
wind_speed(X, Y) ~ weibull(2, 8). % This could also be locationd dependant
% We do not explicitly model wind_direction, since it has no large influence on the ship's movement.

stormy(X, Y) :- wind_speed(X, Y) > 20.

expected_waves(X, Y) ~ normal(0.5, 0.2) :- not stormy(X, Y).
expected_waves(X, Y) ~ normal(2, 0.5) :- stormy(X, Y).

% The surrounding landscape
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

anchoring_ground(X, Y) :- over(X, Y, 'anchoring').  % TODO this is not nessesary?
% ... this is loaded from the chart data

over(X, Y, 'shipping_lane_east').
% ... this is loaded from the chart data
shipping_lane(X, Y, 'east') :- over(X, Y, 'shipping_lane_east').
% ... same for other directions
shipping_lane(X, Y) :- shipping_lane(X, Y, _).

indetermined(X, Y) :- not anchoring_ground(X, Y), not shipping_lane(X, Y).

% -5 means 5m below mean sea level
% Positive depths are fine, thats actually what we call land area
chart_depth(X, Y) ~ normal(-5, 0.5).
% ... this is loaded from the chart data

% Again, negative depths are fine, this gets added to chart_depth witht he same sign
tide ~ normal(0.4, 0.1).

% Our ship
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

% TODO: there is not egecontric view, we model this for all ships!
this_draft ~ normal(5, 0.5).

prev_speed ~ finite([1.0:17.3]).  % this maybe needs to be a placeholder for the program template?
speed ~ finite([1.0:17.6]).  % this maybe needs to be a placeholder for the program template?

heading('east').  % determined by the ship's compass

% The actual model
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

is_safe_depth(X, Y) :- D + T + this_draft + expected_waves < 0.5, chart_depth(X, Y, D), tide(X, Y, T).

0.8::was_anchoring :- prev_speed < 0.2.
0.8::is_anchoring :- speed < 0.2.

is_legal :- indetermined(X, Y).  % You can go anywhere where there are no special rules
is_legal :- anchoring_ground, speed < 10.0.
is_legal :- shipping_lane(curr_X, curr_Y, H), heading(H).

is_safe :- is_safe_depth, not extremely_stormy(curr_X, curr_Y).

likely_behaviour :- is_safe, is_legal.

% Queries
% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% query(likely_behaviour(ship_367121040)).
