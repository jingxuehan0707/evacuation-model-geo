from mesa_geo import GeoAgent
   
class GMModelLegacy:
    def __init__(self, model, car_ahead: GeoAgent, car_follow: GeoAgent):  
        self.car_ahead = car_ahead
        self.car_follow = car_follow
        self.space_hw_threshold = 6 * model.meter_to_feet # Convert 6 feet to meters
        self.max_speed = model.max_speed 
        self.acceleration = model.acceleration
        self.alpha = model.alpha
        self.step_interval = model.step_interval

    def update_speed(self):
        updated_speed = self.car_follow.speed
        if self.car_ahead:
            space_hw = self.car_follow.geometry.distance(self.car_ahead.geometry)  # Space headway
            speed_diff = self.car_ahead.speed - self.car_follow.speed  # Speed difference
            print(f"Space headway: {space_hw}, Speed difference: {speed_diff}, car_follow_id: {self.car_follow.unique_id}, car_ahead_id: {self.car_ahead.unique_id}")
            
            if space_hw < self.space_hw_threshold:
                updated_speed = 0  # Stop if too close
            else:
                # convert alpha from mi^2/hr to m^2/s
                # acceleration = alpha * (car_follow_speed^0 / space_hw^2) * speed_diff
                acc = (self.alpha * 719.44) * (self.car_follow.speed ** 0) / (space_hw ** 2) * speed_diff
                delta_speed = acc * self.step_interval
                updated_speed += delta_speed
            
            if self.car_follow.speed > (space_hw - self.space_hw_threshold) / self.step_interval:
                updated_speed = min((space_hw - self.space_hw_threshold) / self.step_interval, self.car_ahead.speed)
            
            updated_speed = min(updated_speed, self.max_speed)  # Cap to max speed
            updated_speed = max(updated_speed, 0)  # No negative speed
        else:
            if self.car_follow.speed < self.max_speed:
                delta_speed = self.acceleration * self.step_interval
                updated_speed += delta_speed
            
            updated_speed= min(updated_speed, self.max_speed)  # Cap to max speed

        return updated_speed