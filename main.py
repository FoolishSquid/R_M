# main.py
import time
import config as cfg
import hardware as hw
from navigation import Navigator

nav = Navigator()
last_move = None

def scan_and_map_perimeters():
    """ Sweeps all 4 sides, logs walls (ultrasonic) and black traps (RGB) """
    dists = hw.get_ultrasonic_distances()
    visits = {"NORTH": 999, "EAST": 999, "SOUTH": 999, "WEST": 999}
    colors = {"NORTH": "NORMAL", "EAST": "NORMAL", "SOUTH": "NORMAL", "WEST": "NORMAL"}

    directions = [
        ("NORTH", nav.x, nav.y + 1), ("EAST", nav.x + 1, nav.y),
        ("SOUTH", nav.x, nav.y - 1), ("WEST", nav.x - 1, nav.y)
    ]

    for d_name, tx, ty in directions:
        if nav.is_valid_cell(tx, ty):
            if dists[d_name] > cfg.WALL_THRESHOLD_CM and nav.maze[tx][ty] != 99:
                colors[d_name] = hw.get_tile_color(d_name)
                if colors[d_name] == "BLACK":
                    nav.mark_wall(tx, ty)
                else:
                    visits[d_name] = nav.maze[tx][ty]
            else:
                nav.mark_wall(tx, ty)
                
    return visits, colors

try:
    print("Booting Modular Nav-Core...")
    time.sleep(2)
    
    while nav.state != "FINISHED":
        # 1. CHECK MILESTONES
        if nav.state == "EXPLORING" and nav.x == cfg.GOAL_X and nav.y == cfg.GOAL_Y:
            nav.state = "RETURNING"
            hw.stop_motors(force=True)
            hw.buzzer.blink(on_time=0.1, off_time=0.1, n=5, background=False)
            time.sleep(0.5)

        elif nav.state == "RETURNING" and nav.x == cfg.START_X and nav.y == cfg.START_Y:
            nav.state = "FINISHED"
            hw.stop_motors(force=True)
            hw.buzzer.on(); time.sleep(1.0); hw.buzzer.off()
            break

        # 2. ACQUIRE ENVIRONMENTAL DATA
        visits, colors = scan_and_map_perimeters()

        # 3. ASK NAVIGATOR FOR DECISION
        move_decision = None
        target_color = "NORMAL"

        if nav.state == "EXPLORING":
            min_v = min(visits.values())
            if min_v == 999: # Stuck
                next_target = nav.find_nearest_unvisited()
                if next_target:
                    move_decision = nav.get_fastest_path_move(next_target[0], next_target[1])
                else:
                    move_decision = nav.get_fastest_path_move(cfg.GOAL_X, cfg.GOAL_Y)
            else:
                # Find the direction with the minimum visits
                for d_name, v in visits.items():
                    if v == min_v:
                        move_decision = d_name
                        target_color = colors[d_name]
                        break

        elif nav.state == "RETURNING":
            move_decision = nav.get_fastest_path_move(cfg.START_X, cfg.START_Y)
            if move_decision: target_color = colors[move_decision]

        # 4. EXECUTE HARDWARE ACTION
        if move_decision != last_move:
            hw.stop_motors(force=True) 

        if move_decision:
            hw.slide(move_decision)
            nav.update_position(move_decision)
        else:
            # Fatal trap recovery
            nav.x, nav.y = nav.last_silver
            last_move = None
            continue

        last_move = move_decision

        # 5. POST-MOVE MEMORY & PENALTY PROCESSING
        nav.record_tile_visit(target_color)

        if target_color == "BLUE":
            nav.draw_map()
            hw.trigger_blue_penalty()
            last_move = None # Reset physical momentum

        nav.draw_map()

except KeyboardInterrupt:
    print("\nMission Aborted by User.")
    hw.stop_motors(force=True)