% UAV properties
initial_charge ~ normal(90, 5).
charge_cost ~ normal(-0.1, 0.2).
weight ~ normal(0.2, 0.1).
speed ~ normal(10, 5).
height ~ normal(50, 10).

% Pilot properties
registered.
online_training.
practical_training.

% Weather data
1/10::fog; 9/10::clear.

% Visual line of sight given?
vlos(R, C) :- 
    fog, distance(R, C, operator) < 250;
    clear, distance(R, C, operator) < 500;
    clear, over(R, C, bay), distance(R, C, operator) < 900.

% Rules and classification for the OPEN category
open_flight(R, C) :- 
    registered, vlos(R, C), 
    height < 120, weight < 25.

% Sufficient charge is defined to be
% enough to return to the operator
can_return(R, C) :-
    B is initial_charge,
    O is charge_cost,
    D is distance(R, C, start),
    0 < B + (2 * O * D).

% We assume to have a special permit for
% service roads and the bay area
permit(R, C) :- 
    distance(R, C, service) < 15;
    over(R, C, bay).

% Definition of a valid mission
landscape(R, C) :- open_flight(R, C), permit(R, C), can_return(R, C).
