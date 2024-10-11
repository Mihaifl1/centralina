#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "Kablem";  // SSID-ul rețelei Wi-Fi
const char* password = "Kablem325$";  // Parola Wi-Fi

const int ledPin = D1;  // Pin-ul care citește semnalul de 12V (prin divizor de tensiune)
const char* server = "http://192.168.66.239/insert_data.php";  // URL-ul pentru scriptul PHP

WiFiClient client;  // Creează un obiect WiFiClient

String nomeBanco = "A AA";  // Variabila pentru NomeBanco

void setup() {
  Serial.begin(115200);
  pinMode(ledPin, INPUT);  // Setează pinul D1 ca intrare

  // Conectare la Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Conectare la Wi-Fi...");
  }
  Serial.println("Conectat la Wi-Fi!");
}

void loop() {
  int ledState = digitalRead(ledPin);  // Citește starea pinului D1

  // Dacă semnalul este HIGH (3.3V), trimitem date la server
  if (ledState == HIGH) {
    Serial.println("Semnal detectat, trimit date...");

    if (WiFi.status() == WL_CONNECTED) {  // Verificăm dacă suntem conectați la Wi-Fi
      HTTPClient http;
      
      // Creăm URL-ul cu variabila `nomeBanco` pentru NomeBanco și Esito ca OK
      String url = String(server) + "?NomeBanco=" + nomeBanco + "&Esito=OK";

      http.begin(client, url);  // Inițializăm conexiunea HTTP folosind WiFiClient și URL-ul
      int httpCode = http.GET();  // Trimiterea cererii

      if (httpCode > 0) {  // Verificăm dacă cererea a avut succes
        String payload = http.getString();
        Serial.println("Răspuns server: " + payload);
      } else {
        Serial.println("Eroare trimitere cerere: " + String(httpCode));
      }
      http.end();  // Încheiem conexiunea HTTP
    } else {
      Serial.println("Wi-Fi nu este conectat");
    }
  }
  delay(1000);  // Așteptăm 1 secundă între verificări
}
