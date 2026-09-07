#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "Navaneesh";
const char* password = "12345678";
const char* mqtt_server = "broker.hivemq.com"; 

WiFiClient espClient;
PubSubClient client(espClient);

const int buttonPin = 0; 
int buttonState = 0;
int lastButtonState = 0;
unsigned long lastMotionTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(buttonPin, INPUT_PULLUP);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  client.setServer(mqtt_server, 1883);
}

void reconnect() {
  while (!client.connected()) {
    String clientId = "ESP32Node-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("MQTT Connected");
    } else {
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // 1. Simulate Door Sensor
  buttonState = digitalRead(buttonPin);
  if (buttonState != lastButtonState) {
    if (buttonState == LOW) {
      client.publish("home/door", "OPEN");
      Serial.println("Sent: Door OPEN");
    } else {
      client.publish("home/door", "CLOSED");
      Serial.println("Sent: Door CLOSED");
    }
    lastButtonState = buttonState;
    delay(50); // Debounce
  }

  // 2. Robust 10-Second Timer
  unsigned long currentMillis = millis();
  if (currentMillis - lastMotionTime >= 10000) {
    lastMotionTime = currentMillis; 
    client.publish("home/motion", "DETECTED");
    Serial.println("Timer Fired: Sent Motion DETECTED");
  }
}