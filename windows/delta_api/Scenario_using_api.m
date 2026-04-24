% Scenario_using_api.m
% Simple API usage scenario in MATLAB

function Scenario_using_api()
    global BASE_URL;
    BASE_URL = 'http://127.0.0.1:5000';
    
    fprintf('Starting Test Scenario...\n');
    fprintf('Please ensure that app.py is running in the background and serving the API.\n\n');
    
    % 1. Read current positions
    get_positions();
    pause(1); % MATLAB's pause uses seconds
    
    % 2. Move above the object
    move_to(0, 0, -200, 1500); % Trajectory movement (1.5 seconds)
    delay_cmd(500);
    
    % 3. Move down slowly (or directly)
    move_to(0, 0, -250, []); % Direct movement
    delay_cmd(500);
    
    % 4. Grab the object
    grab(1);
    delay_cmd(500);
    
    % 5. Move back up
    move_to(0, 0, -200, 1000);
    delay_cmd(500);
    
    % 6. Move to target location (e.g., X=50, Y=50)
    move_to(50, 50, -200, 2000);
    delay_cmd(500);
    
    % 7. Move down at the target location
    move_to(50, 50, -250, []);
    delay_cmd(500);
    
    % 8. Release the object
    grab(0);
    delay_cmd(500);
    
    % 9. Return to start (center) position
    move_to(0, 0, -200, 1500);
    
    % 10. Check final status again
    get_positions();
    
    fprintf('\nScenario Completed!\n');
end

function get_positions()
    global BASE_URL;
    fprintf('\n--- Getting Positions ---\n');
    options = weboptions('Timeout', 10);
    try
        ee_pos = webread([BASE_URL '/get_ee_pos'], options);
        fprintf('End-Effector Position: \n');
        disp(ee_pos);
        
        mot_pos = webread([BASE_URL '/get_mot_pos'], options);
        fprintf('Motor Positions: \n');
        disp(mot_pos);
    catch e
        fprintf('Error connecting to API (Is the server running?): %s\n', e.message);
    end
end

function move_to(x, y, z, ms)
    global BASE_URL;
    fprintf('\n--- Moving to: (%g, %g, %g) ---\n', x, y, z);
    
    data = struct('x', x, 'y', y, 'z', z);
    options = weboptions('MediaType', 'application/json', 'Timeout', 20); % Increased timeout for long moves
    
    try
        if ~isempty(ms)
            data.ms = ms;
            fprintf('Trajectory movement (%g ms)\n', ms);
            response = webwrite([BASE_URL '/move_pos_traj'], data, options);
        else
            fprintf('Direct movement\n');
            response = webwrite([BASE_URL '/move_pos'], data, options);
        end
        fprintf('Response: \n');
        disp(response);
    catch e
        fprintf('Error sending move command: %s\n', e.message);
    end
end

function grab(state)
    global BASE_URL;
    if state
        action = 'Grabbing';
    else
        action = 'Releasing';
    end
    fprintf('\n--- %s ---\n', action);
    
    data = struct('state', state);
    options = weboptions('MediaType', 'application/json', 'Timeout', 10);
    
    try
        response = webwrite([BASE_URL '/grab'], data, options);
        fprintf('Response: \n');
        disp(response);
    catch e
        fprintf('Error sending grab command: %s\n', e.message);
    end
end

function delay_cmd(ms)
    global BASE_URL;
    fprintf('\n--- Waiting: %g ms ---\n', ms);
    
    data = struct('ms', ms);
    options = weboptions('MediaType', 'application/json', 'Timeout', 10 + (ms/1000));
    
    try
        response = webwrite([BASE_URL '/delay'], data, options);
        fprintf('Response: \n');
        disp(response);
    catch e
        fprintf('Error sending delay command: %s\n', e.message);
    end
end
