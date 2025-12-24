from dataclasses import dataclass
from typing import Optional, Dict

from simulate import closing_speed, compute_ttc


from dataclasses import dataclass
from typing import Optional, Dict

from simulate import closing_speed, compute_ttc


@dataclass
class Scenario:
    name: str
    initial_distance_m: float
    ego_speed_mps: float
    lead_speed_mps: float
    confidence: float
    duration_s: float = 10.0
    dt: float = 0.1

    cut_in_time_s: Optional[float] = None
    cut_in_distance_m: Optional[float] = None
    cut_in_lead_speed_mps: Optional[float] = None


@dataclass
class ScenarioResult:
    fcw_time_s: Optional[float]
    aeb_time_s: Optional[float]
    final_distance_m: float
    min_ttc_s: Optional[float]
    min_distance_m: float
    impact_speed_mps: float


def run_scenario(
    s: Scenario,
    fcw_ttc_s: float = 3.0,
    aeb_ttc_s: float = 1.5,
    aeb_conf_threshold: float = 0.6,
    aeb_decel_mps2: float = 7.0,
) -> ScenarioResult:
    t = 0.0
    distance = s.initial_distance_m
    ego_v = s.ego_speed_mps
    lead_v = s.lead_speed_mps

    min_ttc = None
    min_distance = distance
    impact_speed = 0.0

    fcw_time = None
    aeb_time = None

    cut_in_applied = False
    steps = int(s.duration_s / s.dt)
    for _ in range(steps):
        

        # Handle cut-in event
        if (not cut_in_applied) and s.cut_in_time_s is not None and t >= s.cut_in_time_s:
            distance = s.cut_in_distance_m
            lead_v = s.cut_in_lead_speed_mps
            cut_in_applied = True


        cs = closing_speed(ego_v, lead_v)
        ttc = compute_ttc(distance, cs)

        # Track minimum TTC (only when defined)
        if ttc is not None:
            if min_ttc is None or ttc < min_ttc:
                min_ttc = ttc

        # Track minimum distance
        if distance < min_distance:
            min_distance = distance


        # FCW trigger (warning only)
        if fcw_time is None:
            if ttc is not None and ttc < fcw_ttc_s:
                fcw_time = t

        # AEB trigger (braking decision)
        if aeb_time is None:
            if (
                ttc is not None
                and ttc < aeb_ttc_s
                and s.confidence >= aeb_conf_threshold
                ):
                aeb_time = t
        
        # Apply braking after AEB triggers (simple model)
        if aeb_time is not None:
             ego_v = max(0.0, ego_v - aeb_decel_mps2 * s.dt)



        # Phase 2 simplification: no braking dynamics yet (we're just testing triggers)
        distance = distance + (lead_v - ego_v) * s.dt
        t += s.dt

        if distance <= 0:
            impact_speed = ego_v
            break

        # If not closing anymore, we can stop early
        # BUT don't stop if a future cut-in is scheduled and hasn't happened yet
        if ego_v <= lead_v and distance > 0 and (s.cut_in_time_s is None or cut_in_applied):
            break


    

    return ScenarioResult(fcw_time, aeb_time, distance, min_ttc, min_distance, impact_speed)


def build_scenarios() -> Dict[str, Scenario]:
    return {
        "normal": Scenario(
            name="Normal approach (high confidence)",
            initial_distance_m=60.0,
            ego_speed_mps=25.0,
            lead_speed_mps=15.0,
            confidence=0.9,
        ),
        "low_conf_real_obstacle": Scenario(
            name="Real obstacle, low confidence",
            initial_distance_m=60.0,
            ego_speed_mps=25.0,
            lead_speed_mps=15.0,
            confidence=0.3,
        ),

        "cut_in": Scenario(
            name="Sudden cut-in (high confidence)",
            initial_distance_m=200.0,     # effectively no object initially
            ego_speed_mps=25.0,
            lead_speed_mps=25.0,          # same speed initially
            confidence=0.9,
            duration_s=10.0,
            cut_in_time_s=2.5,            # object appears at 2.5s
            cut_in_distance_m=20.0,       # very close suddenly
            cut_in_lead_speed_mps=15.0,   # slower vehicle cuts in
        ),

    }


if __name__ == "__main__":

    scenarios = build_scenarios()
    for s in scenarios.values():
        r = run_scenario(s)
        print(f"\nScenario: {s.name}")
        print(f"  FCW time: {r.fcw_time_s}")
        print(f"  AEB time: {r.aeb_time_s}")
        print(f"  Final distance: {r.final_distance_m:.2f} m")
        print(f"  Min TTC: {r.min_ttc_s}")
        print(f"  Min distance: {r.min_distance_m:.2f} m")
        print(f"  Impact speed: {r.impact_speed_mps:.2f} m/s")


