#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <FS.h>  // Include SPIFFS for reading and writing to flash
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <ESP8266WebServer.h>

// Wi-Fi network details
const char* ssid = "Kablem";  
const char* password = "Kablem325$";  

// Server details
const char* server = "http://192.168.66.239/insert_data1.php";

// Global variables
String nomeBanco = "C(FF)";  // Example NomeBanco
String codUnic;  // Unique code
String wifiStatus = "Căutare rețele Wi-Fi...";  // Wi-Fi status message
String ultimulSemnal = "Niciun semnal trimis";  // Last signal sent status
String dataOraCurenta;  // Current date and time
String raspunsServer = "Niciun răspuns";  // Server response
int hourOffset = 0;  // Hour offset
int serialNumber = 0;  // Variabilă globală pentru numărul serial

// NTP objects for getting time
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "129.250.35.250", 7200, 60000);  // Server NTP extern cu IP fix

// Web server for the hotspot
ESP8266WebServer serverWeb(80); 

// WiFiClient object for HTTP requests
WiFiClient client;

// Define static IP details
IPAddress local_IP(192, 168, 66, 86);  // Static IP address
IPAddress gateway(192, 168, 66, 254);  // Gateway address (router)
IPAddress subnet(255, 255, 254, 0);    // Subnet mask

// Function to generate a unique code from NomeBanco and a dynamic 6-digit number
String genereazaCodUnic() {
  int codDinamic = random(100000, 999999);  // Generate a 6-digit number
  return nomeBanco + String(codDinamic);  // Combine NomeBanco with the dynamic number
}

// Function to read the unique code from SPIFFS
String citesteCodUnic() {
  if (SPIFFS.exists("/codUnic.txt")) {
    File file = SPIFFS.open("/codUnic.txt", "r");
    if (file) {
      String cod = file.readStringUntil('\n');
      file.close();
      return cod;
    }
  }
  return "";  // Return an empty string if the code doesn't exist
}
void handleLastSignal() {
  serverWeb.send(200, "text/plain", ultimulSemnal);
}

void saveSerialNumber(int serial) {
  File file = SPIFFS.open("/serialNumber.txt", "w");
  if (file) {
    file.println(serial);
    file.close();
  } else {
    Serial.println("Failed to save serial number");
  }
}

int loadSerialNumber() {
  if (SPIFFS.exists("/serialNumber.txt")) {
    File file = SPIFFS.open("/serialNumber.txt", "r");
    if (file) {
      int savedSerial = file.readStringUntil('\n').toInt();
      file.close();
      return savedSerial;
    }
  }
  return 0;  // Default to 0 if no serial number is found
}
// Function to save the unique code in SPIFFS
void salveazaCodUnic(String cod) {
  File file = SPIFFS.open("/codUnic.txt", "w");
  if (file) {
    file.println(cod);
    file.close();
  }
}

// Function to save the hour offset in SPIFFS
void saveOffset(int offset) {
  File file = SPIFFS.open("/hourOffset.txt", "w");
  if (file) {
    file.println(offset);
    file.close();
  } else {
    Serial.println("Failed to save hour offset");
  }
}

// Function to load the hour offset from SPIFFS
int loadOffset() {
  if (SPIFFS.exists("/hourOffset.txt")) {
    File file = SPIFFS.open("/hourOffset.txt", "r");
    if (file) {
      int savedOffset = file.readStringUntil('\n').toInt();
      file.close();
      return savedOffset;
    }
  }
  return 0;  // Default to 0 if no offset is found
}

// Funcție pentru a mări offset-ul orei
void handleIncreaseHourOffset() {
  hourOffset++;
  saveOffset(hourOffset);  // Salvează noul offset
  Serial.println("Hour offset increased to: " + String(hourOffset));
  serverWeb.send(200, "text/plain", "Hour offset increased to: " + String(hourOffset));
}

// Funcție pentru a micșora offset-ul orei
void handleDecreaseHourOffset() {
  hourOffset--;
  saveOffset(hourOffset);  // Salvează noul offset
  Serial.println("Hour offset decreased to: " + String(hourOffset));
  serverWeb.send(200, "text/plain", "Hour offset decreased to: " + String(hourOffset));
}

// Function to set up a hotspot
void setupHotspot() {
  WiFi.softAP(nomeBanco.c_str(), "password123");  // Configure hotspot with NomeBanco
  IPAddress hotspotIP = WiFi.softAPIP();
  String ssidHotspot = nomeBanco + "-" + hotspotIP.toString();
  
  WiFi.softAP(ssidHotspot.c_str(), "password123");  // Set SSID from NomeBanco and IP
  Serial.println("Hotspot active with SSID: " + ssidHotspot);
  Serial.println("Hotspot IP: " + WiFi.softAPIP().toString());
}

// Function to display the connection process and server response on the browser
void handleRoot() {
  String message = "<html><head>";
  message += "<style>";
  message += "body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; color: #333; }";
  message += "h1 { color: #4CAF50; }";
  message += "p { font-size: 1.2em; }";
  message += ".progress-bar { width: 100%; background-color: #f4f4f4; border: 1px solid #ccc; border-radius: 5px; margin: 10px 0; }";
  message += ".progress { height: 20px; background: linear-gradient(to right, red, orange, yellow, green); border-radius: 5px; }";
  message += "</style>";
  
  message += "<meta http-equiv='refresh' content='5'>";  // Refresh every 5 seconds
  
  message += "<script>";
  // AJAX for current time
  message += "setInterval(function() {";
  message += "  var xhttp = new XMLHttpRequest();";
  message += "  xhttp.onreadystatechange = function() {";
  message += "    if (this.readyState == 4 && this.status == 200) {";
  message += "      document.getElementById('datetime').innerHTML = this.responseText;";
  message += "    }";
  message += "  };";
  message += "  xhttp.open('GET', '/datetime', true);";
  message += "  xhttp.send();";
  message += "}, 2000);";  // 2-second update interval

  // AJAX for server response
  message += "setInterval(function() {";
  message += "  var xhttp = new XMLHttpRequest();";
  message += "  xhttp.onreadystatechange = function() {";
  message += "    if (this.readyState == 4 && this.status == 200) {";
  message += "      var response = this.responseText.split(',');";  // Split the percentage and RSSI value
  message += "      var signalPercent = response[0];";  // First part is percentage
  message += "      var signalStrength = response[1];";  // Second part is RSSI value (in dBm)";
  message += "      document.getElementById('progress').style.width = signalPercent + '%';";  // Update progress bar width
  message += "      document.getElementById('signal-level').innerHTML = signalStrength + ' dBm';";  // Update signal strength display
  message += "    }";
  message += "  };";
  message += "  xhttp.open('GET', '/signal-strength', true);";
  message += "  xhttp.send();";
  message += "}, 2000);";  // 2-second update interval

  message += "</script></head><body>";
  message += "<h1>Wi-Fi Connection Status:</h1>";
  message += "<p>" + wifiStatus + "</p>";
  message += "<p>Last signal sent: " + ultimulSemnal + "</p>";
  
  if (WiFi.status() == WL_CONNECTED) {
    int signalStrength = WiFi.RSSI();  // Wi-Fi signal strength
    message += "<p>Connected to Wi-Fi! Signal strength: <span id='signal-level'>" + String(signalStrength) + " dBm</span></p>";
    message += "<p>IP address: " + WiFi.localIP().toString() + "</p>";
    message += "<p>Current time: <span id='datetime'>" + dataOraCurenta + "</span></p>";
    message += "<p>Server response: <span id='server-response'>" + raspunsServer + "</span></p>";
    
    // Progress bar to display signal strength
    message += "<div class='progress-bar'><div class='progress' id='progress' style='width: 0%;'></div></div>";
  }
  
  message += "</body></html>";
  serverWeb.send(200, "text/html", message);
}

// Function to handle /status endpoint
void handleStatus() {
  int rssi = WiFi.RSSI();  // Get the Wi-Fi signal strength
  
  // Get current date and time from NTP
  timeClient.update();
  dataOraCurenta = getFormattedDate(timeClient.getEpochTime());

  // Build JSON response
  String json = "{";
  json += "\"status\": \"OK\",";
  json += "\"rssi\": " + String(rssi) + ",";
  json += "\"time\": \"" + dataOraCurenta + "\"";
  json += "}";

  // Send JSON response
  serverWeb.send(200, "application/json", json);
}

void handleSignalStrength() {
  if (WiFi.status() == WL_CONNECTED) {
    int signalStrength = WiFi.RSSI();  // Wi-Fi signal strength in dBm

    // Convert the RSSI value (-100 to -50 dBm) to percentage (0 to 100)
    int signalPercent = map(signalStrength, -100, -50, 0, 100);
    signalPercent = constrain(signalPercent, 0, 100);  // Limit values between 0 and 100

    // Send the current RSSI value and percentage for progress bar
    serverWeb.send(200, "text/plain", String(signalPercent) + "," + String(signalStrength));  
  } else {
    // Do not update or reset the values if Wi-Fi is disconnected
    serverWeb.send(200, "text/plain", "-1,-100");  // Sending -1 to indicate no update
  }
}

// Function to send the current date and time
void handleDateTime() {
  serverWeb.send(200, "text/plain", dataOraCurenta);
}

// Function to send the server response
void handleServerResponse() {
  serverWeb.send(200, "text/plain", raspunsServer);
}

void setup() {
  Serial.begin(115200);
  pinMode(D1, INPUT);  // Set D1 as input for detecting 3V signal

  // Initialize SPIFFS
  if (!SPIFFS.begin()) {
    Serial.println("Error initializing SPIFFS");
    return;
  }
  serialNumber = loadSerialNumber();
  // Load the hour offset from SPIFFS
  hourOffset = loadOffset();
  Serial.println("Hour offset loaded: " + String(hourOffset));

serialNumber = loadSerialNumber();
Serial.println("Serial number loaded: " + String(serialNumber));
  // Set up the hotspot
  setupHotspot();

  // Set functions for the web server
  serverWeb.on("/last-signal", handleLastSignal);
  serverWeb.on("/increase-hour", handleIncreaseHourOffset);  // Endpoint pentru a mări offset-ul orei
  serverWeb.on("/decrease-hour", handleDecreaseHourOffset);  // Endpoint pentru a micșora offset-ul orei
  serverWeb.on("/signal-strength", handleSignalStrength);
  serverWeb.on("/status", handleStatus);  // Add the /status endpoint
  serverWeb.on("/", handleRoot);
  serverWeb.on("/datetime", handleDateTime);  // Endpoint for the current time
  serverWeb.on("/server-response", handleServerResponse);  // Endpoint for the server response
  serverWeb.begin();  // Start the web server
  Serial.println("Web server started.");

  // Read the unique code from SPIFFS
  codUnic = citesteCodUnic();
  if (codUnic == "") {
    codUnic = genereazaCodUnic();
    salveazaCodUnic(codUnic);
    Serial.println("Generated and saved unique code: " + codUnic);
  } else {
    Serial.println("Unique code read from memory: " + codUnic);
  }

  // Connect to the Wi-Fi network with a fixed IP, gateway, and subnet
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Failed to configure static IP settings");
  }

  wifiStatus = "Connecting to Wi-Fi...";
  WiFi.begin(ssid, password);
}

void loop() {
  // Handle web server requests
  serverWeb.handleClient();

  // Check Wi-Fi status
  if (WiFi.status() == WL_CONNECTED) {
    wifiStatus = "Connected to Wi-Fi!";
    
    // Check if pin D1 is HIGH (3V is present)
    if (digitalRead(D1) == HIGH) {
      sendToServer();  // Send data to the server when D1 is HIGH
    }

    // Update NTP time
    timeClient.update();  // Update time from NTP
    dataOraCurenta = getFormattedDate(timeClient.getEpochTime());  // Get current date and time
  } else {
    wifiStatus = "Connecting to Wi-Fi...";
  }
}



// Function to send data to the PHP server
void sendToServer() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, server);  // Initialize HTTP connection
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    delay(2000);  // Add delay here before sending data

    // POST data including unique code and current time
    String postData = "NomeBanco=" + nomeBanco + 
                      "&Codice=RI20126002" + 
                      "&RevisioneCablaggio=B" + 
                      "&Data=" + dataOraCurenta + 
                      "&Lotto=2440" + 
                      "&Operatore=165133" + 
                      "&DurataTest=NULL" + 
                      "&LetturaDMC=" + codUnic + 
                      "&Barcode=TBD" + 
                      "&Esito=OK" + 
                      "&Seriale=" + String(serialNumber) + 
                      "&Note=NULL";

    // Send the POST request
    int httpCode = http.POST(postData);

    if (httpCode > 0) {
      raspunsServer = http.getString();  // Get the server's response
      Serial.println("Server response: " + raspunsServer);
       serialNumber++;
      saveSerialNumber(serialNumber);  // Salvăm numărul serial incrementat
      updateUniqueCode();  // Update the unique code after POST
      ultimulSemnal = "Signal sent at: " + dataOraCurenta;  // Update the last signal sent
    } else {
      raspunsServer = "POST error: " + String(httpCode);
      Serial.println(raspunsServer);
    }
    http.end();  // Close the HTTP connection
  }
}

// Function to update the unique code
void updateUniqueCode() {
  String numarParte = codUnic.substring(nomeBanco.length());  // Numeric part of the code
  int numar = numarParte.toInt();  // Convert to int to increment
  numar++;  // Increment the code

  // Form the new unique code
  codUnic = nomeBanco + String(numar);
  salveazaCodUnic(codUnic);  // Save the new unique code in SPIFFS
  Serial.println("Updated and saved unique code: " + codUnic);
}

// Function to format the date and time as "YYYY-MM-DD HH:MM:SS"
String getFormattedDate(unsigned long epochTime) {
  int year = 1970 + epochTime / 31556926;
  int month = (epochTime % 31556926) / 2629743 + 1;
  int day = ((epochTime % 2629743) / 86400) + 1;
  int hour = ((epochTime % 86400 / 3600)) + hourOffset;  // Apply hourOffset
  int minute = (epochTime % 3600) / 60;
  int second = epochTime % 60;

  char dateBuffer[20];
  snprintf(dateBuffer, sizeof(dateBuffer), "%04d-%02d-%02d %02d:%02d:%02d", year, month, day, hour, minute, second);

  return String(dateBuffer);
}
