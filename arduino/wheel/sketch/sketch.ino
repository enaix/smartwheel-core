#include <EncButton.h>

// Pins config
#define clk_port 16 // D0
#define dt_port 5 // D1
#define sw_port 4 // D2

// Serial config
#define serial_rate 9600
#define sw_button_text "sw_button1_press"
#define enc_text "enc1_clockwise"
#define enc_text_hold "enc1_clockwise_hold"

// Denoize config
#define noize_thresh 5

EncButton<EB_TICK, clk_port, dt_port, sw_port> enc;

int enc_pos = 0;
bool enc_pressed = false;
unsigned long sw_time = 0;
unsigned long enc_time = 0;

bool is_debounce(unsigned long *old) {
  unsigned long cur_time = millis();
  unsigned long timing = cur_time - *old;
  if (timing > noize_thresh) {
    *old = cur_time;
    return false;
  }
  return true;
}

/*void setup() {
  // put your setup code here, to run once:
  Serial.begin(serial_rate);
  pinMode(clk_port, INPUT);
  pinMode(dt_port, INPUT);
  pinMode(sw_port, INPUT);
  enc_pos = digitalRead(clk_port);
  enc_pressed = digitalRead(sw_port);
  Serial.println("Starting...");
}

void loop() {
  // put your main code here, to run repeatedly:
  bool sw_down = digitalRead(sw_port);
  if (sw_down != enc_pressed) {
    if (!is_debounce(&sw_time)) {
      Serial.println(String(sw_button_text) + " " + String(bool(sw_down)));
      enc_pressed = sw_down;
    }
  }
  bool clk_u = digitalRead(clk_port);
  bool dt_u = digitalRead(dt_port);
  if (clk_u != enc_pos) {
    if (!is_debounce(&enc_time)){
      if (dt_u != clk_u) {
        Serial.println(String(enc_text) + " true");
      } else {
        Serial.println(String(enc_text) + " false");
      }
      enc_pos = clk_u;
    }
  }
}*/

void setup() {
  Serial.begin(serial_rate);
}

void loop() {
  enc.tick();

  if (enc.isLeft()) {
    Serial.println(String(enc_text) + " false");
  }

  if (enc.isRight()) {
    Serial.println(String(enc_text) + " true");
  }

  if (enc.isLeftH()) {
    Serial.println(String(enc_text_hold) + " false");
  }

  if (enc.isRightH()) {
    Serial.println(String(enc_text_hold) + " true");
  }

  if (enc.isClick()) {
    Serial.println(String(sw_button_text) + " click");
  }

  if (enc.isHold()) {
    Serial.println(String(sw_button_text) + " hold");
  }
}
