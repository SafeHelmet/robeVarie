#include <ArduinoBLE.h>

// BLE UUIDs
const char *deviceServiceUuid = "f47ac10b-58cc-4372-a567-0e02b2c3d479";
const char *deviceServiceRequestCharacteristicUuid = "f47ac10b-58cc-4372-a567-0e02b2c3d480";
const char *deviceServiceResponseCharacteristicUuid = "f47ac10b-58cc-4372-a567-0e02b2c3d481";

// BLE Service and Characteristics
BLEService ledService(deviceServiceUuid);
BLEStringCharacteristic ledRequestCharacteristic(deviceServiceRequestCharacteristicUuid, BLEWrite | BLERead, 4);
BLEStringCharacteristic ledResponseCharacteristic(deviceServiceResponseCharacteristicUuid, BLENotify, 4);

BLEDescriptor cccdDescriptor("f47ac10b-58cc-4372-a567-0e02b2c3d482", "");

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  BLE.setDeviceName("Casco");
  BLE.setLocalName("Casco");

  if (!BLE.begin()) {
    Serial.println("- Starting Bluetooth Low Energy Module Failed");
    while (1); // Halt execution if BLE module fails to initialize
  }

  // Add service and characteristics
  BLE.setAdvertisedService(ledService);
  ledService.addCharacteristic(ledRequestCharacteristic);
  ledService.addCharacteristic(ledResponseCharacteristic);
  ledResponseCharacteristic.addDescriptor(cccdDescriptor);
  BLE.addService(ledService);

  // Initialize response characteristic
  ledResponseCharacteristic.writeValue("1");
  
  // Start advertising
  BLE.advertise();
  Serial.println("Scanning start");
}

void loop() {
  // Check for central device
  BLEDevice central = BLE.central();
  if (central) {
    Serial.println("Connected to central device");

    while (central.connected()) {
      // Handle written values for the request characteristic
      if (ledRequestCharacteristic.written()) {
        String value = ledRequestCharacteristic.value();
        if (value == "ON") {
          digitalWrite(LED_BUILTIN, HIGH);
          Serial.println("LED turned ON");
          ledResponseCharacteristic.writeValue("1");
        } else if (value == "OFF") {
          digitalWrite(LED_BUILTIN, LOW);
          Serial.println("LED turned OFF");
          ledResponseCharacteristic.writeValue("0");
        }
        delay(20);
      }
    }

    Serial.println("Disconnected from central device");
  }
}
