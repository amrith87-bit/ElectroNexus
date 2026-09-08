import paho.mqtt.client as mqtt
import time

# ==================================================
# MQTT SETTINGS
# ==================================================

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883


# ==================================================
# MQTT TOPICS
# ==================================================

MOVEMENT_TOPIC = "home/sensor/movement"
VIBRATION_TOPIC = "home/sensor/vibration"
ACCELERATION_TOPIC = "home/sensor/acceleration"

MOTION_TOPIC = "home/motion"
DOOR_TOPIC = "home/door"


# ==================================================
# SYSTEM STATE
# ==================================================

door_state = "CLOSED"

node_trust_score = 100

movement = 0
vibration = 0
acceleration = 0

movement_trust = 100
vibration_trust = 100
acceleration_trust = 100

combined_trust = 100

previous_anomaly = False

last_penalty_time = 0

PENALTY_COOLDOWN = 5


# ==================================================
# TRUST CALCULATION
# ==================================================

def calculate_trust(value):

    if value < 20:
        return 100

    elif value < 40:
        return 85

    elif value < 60:
        return 70

    elif value < 80:
        return 50

    else:
        return 25


# ==================================================
# CALCULATE COMBINED TRUST
# ==================================================

def calculate_combined_trust():

    global combined_trust

    combined_trust = int(
        (movement_trust * 0.35) +
        (vibration_trust * 0.30) +
        (acceleration_trust * 0.35)
    )


# ==================================================
# DISPLAY DASHBOARD
# ==================================================

def display_dashboard():

    print("\n")
    print("==============================================")
    print("          TRUST CONSENSUS ENGINE")
    print("==============================================")

    print(f"Door State       : {door_state}")

    print("----------------------------------------------")

    print(
        f"Movement         : {movement:3d} "
        f"| Trust: {movement_trust:3d}/100"
    )

    print(
        f"Vibration        : {vibration:3d} "
        f"| Trust: {vibration_trust:3d}/100"
    )

    print(
        f"Acceleration     : {acceleration:3d} "
        f"| Trust: {acceleration_trust:3d}/100"
    )

    print("----------------------------------------------")

    print(f"COMBINED TRUST   : {combined_trust}/100")

    if combined_trust >= 80:

        print("STATUS           : HIGH TRUST")

    elif combined_trust >= 60:

        print("STATUS           : MEDIUM TRUST")

    elif combined_trust >= 40:

        print("STATUS           : LOW TRUST")

    else:

        print("STATUS           : VERY LOW TRUST")

    print("----------------------------------------------")

    print(f"NODE TRUST       : {node_trust_score}/100")

    if node_trust_score <= 0:

        print("NODE STATUS      : QUARANTINED")

    elif node_trust_score < 40:

        print("NODE STATUS      : SUSPICIOUS")

    else:

        print("NODE STATUS      : ACTIVE")

    print("==============================================")


# ==================================================
# MQTT CONNECT
# ==================================================

def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("==============================================")
        print("Consensus Engine Online")
        print("Connected to MQTT Broker")
        print("Monitoring 3 virtual sensors...")
        print("==============================================")

        client.subscribe(MOVEMENT_TOPIC)
        client.subscribe(VIBRATION_TOPIC)
        client.subscribe(ACCELERATION_TOPIC)

        client.subscribe(MOTION_TOPIC)
        client.subscribe(DOOR_TOPIC)

    else:

        print("MQTT connection failed.")
        print("Error code:", rc)


# ==================================================
# MQTT MESSAGE
# ==================================================

def on_message(client, userdata, msg):

    global movement
    global vibration
    global acceleration

    global movement_trust
    global vibration_trust
    global acceleration_trust

    global door_state
    global node_trust_score

    global previous_anomaly
    global last_penalty_time

    topic = msg.topic

    payload = msg.payload.decode("utf-8")


    # ==============================================
    # DOOR SENSOR
    # ==============================================

    if topic == DOOR_TOPIC:

        door_state = payload

        print(f"[DOOR] Door is {door_state}")


    # ==============================================
    # MOVEMENT SENSOR
    # ==============================================

    elif topic == MOVEMENT_TOPIC:

        try:

            movement = int(float(payload))

            movement_trust = calculate_trust(movement)

        except ValueError:

            print("[ERROR] Invalid movement value")


    # ==============================================
    # VIBRATION SENSOR
    # ==============================================

    elif topic == VIBRATION_TOPIC:

        try:

            vibration = int(float(payload))

            vibration_trust = calculate_trust(vibration)

        except ValueError:

            print("[ERROR] Invalid vibration value")


    # ==============================================
    # ACCELERATION SENSOR
    # ==============================================

    elif topic == ACCELERATION_TOPIC:

        try:

            acceleration = int(float(payload))

            acceleration_trust = calculate_trust(acceleration)

        except ValueError:

            print("[ERROR] Invalid acceleration value")


    # ==============================================
    # MOTION DETECTION
    # ==============================================

    elif topic == MOTION_TOPIC:

        if payload == "DETECTED":

            print("[SENSOR] Motion detected.")

        else:

            print("[SENSOR] No significant motion.")


    # ==============================================
    # CALCULATE COMBINED TRUST
    # ==============================================

    calculate_combined_trust()


    # ==============================================
    # ANOMALY DETECTION
    # ==============================================

    movement_detected = (
        movement > 50 or
        vibration > 50 or
        acceleration > 50
    )

    anomaly = (
        movement_detected and
        door_state == "CLOSED"
    )


    # ==============================================
    # TRUST PENALTY
    # ==============================================

    current_time = time.time()

    if anomaly and not previous_anomaly:

        if current_time - last_penalty_time >= PENALTY_COOLDOWN:

            print()
            print(
                "[WARNING] IMPOSSIBILITY DETECTED!"
            )

            print(
                "Movement detected while door is CLOSED."
            )

            node_trust_score -= 20

            if node_trust_score < 0:

                node_trust_score = 0

            last_penalty_time = current_time

            print(
                f"[SYSTEM] Node Trust Score: "
                f"{node_trust_score}/100"
            )

            if node_trust_score <= 0:

                print(
                    "[ALERT] QUARANTINE TRIGGERED!"
                )

                print(
                    "[ALERT] ESP32 node has been isolated."
                )


    # ==============================================
    # VALID SENSOR EVENT
    # ==============================================

    elif movement_detected and door_state == "OPEN":

        print(
            "[SYSTEM] Motion validated."
        )

        print(
            "[SYSTEM] Door is OPEN."
        )


    previous_anomaly = anomaly


    # ==============================================
    # DISPLAY
    # ==============================================

    display_dashboard()


# ==================================================
# CREATE MQTT CLIENT
# ==================================================

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message


# ==================================================
# CONNECT TO BROKER
# ==================================================

print("Connecting to MQTT broker...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)


# ==================================================
# START MQTT LOOP
# ==================================================

client.loop_forever()