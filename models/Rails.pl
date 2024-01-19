% UAV properties
initial_charge ~ normal(90, 5).
charge_cost ~ normal(-0.1, 0.2).

% Sufficient charge is defined to be
% enough to return to the operator
can_return(R, C) :-
    B is initial_charge,
    O is charge_cost,
    D is distance(R, C, start),
    0 < B + (2 * O * D).

% Stay close to rails and keep enough battery charge to return
landscape(R, C) :- distance(R, C, rail) < 5, can_return(R, C).
