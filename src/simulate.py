def closing_speed(ego_speed_mps: float, lead_speed_mps: float) -> float:

     return ego_speed_mps - lead_speed_mps 



def compute_ttc(distance_m: float, closing_speed_mps: float):
    if closing_speed_mps <= 0:
        return None  # not closing, no collision risk

    if distance_m <= 0:
        return 0.0   # already at collision

    return distance_m / closing_speed_mps

if __name__ == "__main__":
    ego = 25.0
    lead = 15.0
    dist = 50.0

    cs = closing_speed(ego, lead)
    ttc = compute_ttc(dist, cs)

    print("Closing speed:", cs)   # expect +10
    print("TTC:", ttc)            # expect ~5.0
