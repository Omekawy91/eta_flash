from flask import Flask, request, jsonify
import openrouteservice
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta, date

app = Flask(__name__)
ORS_API_KEY = "5b3ce3597851110001cf624838ed54901e044a6aa4d688103f2b9208"
client = openrouteservice.Client(key=ORS_API_KEY)
geolocator = Nominatim(user_agent="meeting-app")
today = date.today()

def get_coordinates(place):
    location = geolocator.geocode(place, timeout=10)
    if location:
        return (location.longitude, location.latitude)
    else:
        raise Exception(f"Invalid location: {place}")

def get_travel_time(user_coords, meeting_coords, mode="driving-car"):
    route = client.directions(
        coordinates=[user_coords, meeting_coords],
        profile=mode,
        format='json'
    )
    duration_sec = route['routes'][0]['summary']['duration']
    return duration_sec / 60  # return in minutes

@app.route("/eta", methods=["POST"])
def eta():
    data = request.json
    try:
        user_place = data["user_place"]
        meeting_place = data["meeting_place"]
        current_time = datetime.strptime(data["current_time"], "%I:%M %p")
        meeting_time = datetime.strptime(data["meeting_time"], "%I:%M %p")
        current_time = datetime.combine(today, current_time.time())
        meeting_time = datetime.combine(today, meeting_time.time())

        user_coords = get_coordinates(user_place)
        meeting_coords = get_coordinates(meeting_place)
        travel_minutes = get_travel_time(user_coords, meeting_coords)
        arrival_time = current_time + timedelta(minutes=travel_minutes)

        if arrival_time > meeting_time:
            delay_minutes = round((arrival_time - meeting_time).total_seconds() / 60)
            return jsonify({ "status": "late", "delay": delay_minutes })
        else:
            return jsonify({ "status": "on_time", "eta": round(travel_minutes) })

    except Exception as e:
        return jsonify({ "error": str(e) }), 400

if __name__ == "__main__":
    app.run(debug=True)