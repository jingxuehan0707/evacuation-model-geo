from mesa_geo import GeoAgent
import math
class GMModel:

    def __init__(self, model, car_ahead: GeoAgent, car_follow: GeoAgent):
        self.car_ahead = car_ahead
        self.car_follow = car_follow
        self.space_headway_threshold = 2 # Space headway threshold in meters
        self.max_speed = 10 # m/s
        self.acceleration = 1.524 # m/s^2
        # self.alpha = 0.14 # alpha parameter of the car-following model is set to 0.14 mi2/hr (free-flow speed = 35 mph & jam density = 250 veh/mi/lane)
        self.alpha = 0.14 * 719.444  # 0.14 is mi2/hr, convert to m2/s
        self.step_interval = model.step_interval

    def update_speed(self):
        updated_speed = self.car_follow.speed
        if self.car_ahead:
            space_hw = self.car_follow.geometry.distance(self.car_ahead.geometry)  # Space headway
            speed_diff = self.car_follow.speed - self.car_ahead.speed  # Speed difference
            
            if space_hw < 2:
                updated_speed = 0  # Stop if too close
            else:
                acc = self.alpha * ((self.car_follow.speed) ** 0) / ((space_hw) ** 2) * speed_diff
                delta_speed = acc * self.step_interval
                updated_speed += delta_speed
            
            if self.car_follow.speed > (space_hw - 2) / self.step_interval:
                updated_speed = min((space_hw - 2) / self.step_interval, self.car_ahead.speed)
            
            updated_speed = min(updated_speed, self.max_speed)  # Cap to max speed
            updated_speed = max(updated_speed, 0)  # No negative speed
        else:
            if self.car_follow.speed < self.max_speed:
                delta_speed = self.acceleration * self.step_interval
                updated_speed += delta_speed
            
            updated_speed= min(updated_speed, self.max_speed)  # Cap to max speed

        return updated_speed
    
class GMModelLegacy:
    def __init__(self, model, car_ahead: GeoAgent, car_follow: GeoAgent):  
        self.car_ahead = car_ahead
        self.car_follow = car_follow
        self.space_headway_threshold = 6 # Space headway threshold in feet
        self.max_speed = model.max_speed 
        self.acceleration = model.acceleration
        self.alpha = model.alpha
        self.step_interval = model.step_interval

    def update_speed(self):
        updated_speed = self.car_follow.speed
        if self.car_ahead:
            space_hw = self.car_follow.geometry.distance(self.car_ahead.geometry)  # Space headway
            speed_diff = self.car_follow.speed - self.car_ahead.speed  # Speed difference
            
            if space_hw < 6:
                updated_speed = 0  # Stop if too close
            else:
                # convert alpha from mi^2/hr to ft^2/s
                acc = (self.alpha * 719.44) * (self.car_follow.speed ** 2) / (space_hw ** 2) * speed_diff
                delta_speed = acc * self.step_interval
                updated_speed += delta_speed
            
            if self.car_follow.speed > (space_hw - 6) / self.step_interval:
                updated_speed = min((space_hw - 6) / self.step_interval, self.car_ahead.speed)
            
            updated_speed = min(updated_speed, self.max_speed)  # Cap to max speed
            updated_speed = max(updated_speed, 0)  # No negative speed
        else:
            if self.car_follow.speed < self.max_speed:
                delta_speed = self.acceleration * self.step_interval
                updated_speed += delta_speed
            
            updated_speed= min(updated_speed, self.max_speed)  # Cap to max speed

        return updated_speed