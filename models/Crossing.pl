% Traffic light for pedestrians is green
green_light.

% Crossings can be used if the traffic light is green
% Also, the UAV needs to keep a safe distance to the surrounding tertiary roads
landscape(R, C) :- 
    distance(R, C, crossing) < 5, green_light;
    distance(R, C, tertiary) > 10.
