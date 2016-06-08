class TMCUpdateClass:
    level_of_service = 1
    expected_level_of_service = 2
    accidents = 3
    incidents = 4
    closures_and_lane_restrictions = 5
    carriageway_restrictions = 6
    exit_restrictions = 7
    entry_restrictions = 8
    traffic_restrictions = 9
    carpool_information = 10
    roadworks = 11
    obstruction_hazards = 12
    dangerous_situations = 13
    road_conditions = 14
    temperaures = 15
    precipitation_and_visibility = 16
    wind_and_air_quality = 17
    activities = 18
    security_alerts = 19
    delays = 20
    cancellations = 21
    travel_time_information = 22
    dangerous_vehicles = 23
    exceptional_loads_vehicles = 24
    traffic_equipment_status = 25
    size_and_weight_limits = 26
    parking_restrictions = 27
    parking = 28
    reference_to_audio_broadcast = 29
    service_messages = 30
    special_messages = 31

    level_of_service_forecast = 32
    weather_forecast = 33
    road_conditions_forecast = 34
    environment = 35
    wind_forecast = 36
    temperature_forecast = 37
    delay_forecast = 38
    cancellation_forecast = 39

    NONE = 9999

    # Set penalization for specific class
    # becouse interval 0-1 is too large, we divide this values by 2
    # real penalty for each edge is sum of lifetime penalties + 1
    # real penalty is multiplated by edge lengths
    ClassToPenalization = {
        accidents : 3,

        incidents : 1.5,

        closures_and_lane_restrictions : 0.5,
        traffic_restrictions : 1,
        carriageway_restrictions : 0.5,
        exit_restrictions : 0.8,
        entry_restrictions : 0.8,
    
        obstruction_hazards : 0.3,
        dangerous_situations : 1.5,
        dangerous_vehicles : 0.8,
        exceptional_loads_vehicles : 0.3,


        NONE : 0

}