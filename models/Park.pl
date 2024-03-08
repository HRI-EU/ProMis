% UAV properties
1.0::standard; 0.0::special.
initial_charge ~ normal(90, 5).
charge_cost ~ normal(-0.2, 0.1).
weight ~ normal(2.0, 0.1).

% Weather
1/10::fog; 9/10::clear.
0.0::high_altitude.

% Visual line of sight
vlos(R, C) :- 
    fog, distance(R, C, operator) < 250;
    clear, distance(R, C, operator) < 500.

% Simplified OPEN flight category
open_flight(R, C) :- 
    standard, vlos(R, C), weight < 25.

% Sufficient charge is defined to be
% enough to return to the operator
can_return(R, C) :-
    B is initial_charge,
    O is charge_cost,
    D is distance(R, C, operator),
    0 < B + (2 * O * D).

% Special permit for parks and roads
permit(R, C) :- 
    over(R, C, park); 
    distance(R, C, primary) < 15;
    distance(R, C, secondary) < 10;
    distance(R, C, tertiary) < 5.

% The Probabilistic Mission Landscape
landscape(R, C) :- 
    permit(R, C), open_flight(R, C), can_return(R, C);
    special, high_altitude, can_return(R, C).
