// 74HC595 Pins
#define SR_nOE  10  // B6
#define SR_SER  18  // F7
#define SR_CLK  14  // B3
#define SR_RCLK 16  // B2
#define SR_nCLR 15  // B1

// DUT Reset
#define DUT_nRST  19  // F6

// State LEDs
#define LED_OKAY  8   // B4
#define LED_ERROR 9   // B5

// Commands
#define STATE_OKAY  32
#define STATE_ERROR 33
#define STATE_RESET 34

#define HIGH_Z      128
#define HARD_RESET  255

void shift_out(uint32_t bitstream);
void press_key(uint8_t key);

void setup() 
{
  // Shift Reg
  pinMode(SR_nOE, OUTPUT);
  pinMode(SR_SER, OUTPUT);
  pinMode(SR_nCLR, OUTPUT);
  pinMode(SR_CLK, OUTPUT);
  pinMode(SR_RCLK, OUTPUT);
  // Start high Z
  digitalWrite(SR_nOE, HIGH);

  // DUT nRST start high
  pinMode(DUT_nRST, OUTPUT);
  digitalWrite(DUT_nRST, HIGH);

  // LEDs
  pinMode(LED_OKAY, OUTPUT);
  pinMode(LED_ERROR, OUTPUT);
  digitalWrite(LED_OKAY, LOW);
  digitalWrite(LED_ERROR, LOW);

  Serial.begin(115200);
}

void loop() 
{
  while (Serial.available() > 0)
  {
    uint8_t data = Serial.parseInt();

    if (data >= 1 && data <= 18)
    {
      press_key(data);
    }
    else if (data == HIGH_Z)
    {
      digitalWrite(SR_nOE, HIGH);
      digitalWrite(DUT_nRST, HIGH);
      pinMode(DUT_nRST, INPUT);
      Serial.println("High Z IO");
    }
    else if (data == STATE_OKAY)
    {
      digitalWrite(STATE_ERROR, LOW);
      digitalWrite(STATE_OKAY, HIGH);
      Serial.println("State OKAY");
    }
    else if (data == STATE_ERROR)
    {
      digitalWrite(STATE_ERROR, HIGH);
      digitalWrite(STATE_OKAY, LOW);
      Serial.println("State ERROR");
    }
    else if (data == STATE_RESET)
    {
      digitalWrite(STATE_ERROR, LOW);
      digitalWrite(STATE_OKAY, LOW);
      Serial.println("State RESET");
    }
    else if (data == HARD_RESET)
    {
      pinMode(DUT_nRST, OUTPUT);
      digitalWrite(DUT_nRST, LOW);
      delay(50);
      digitalWrite(DUT_nRST, HIGH);
      Serial.println("Hard Reset DUT");
    }
  }
}

void press_key(uint8_t key)
{
  shift_out(0xFFFFFF & ~(key - 1)); // 24 bits, active low, MSB first
  delay(50);
  shift_out(0xFFFFFF); // Release all keys
  delay(1);
  digitalWrite(SR_nOE, HIGH);

  Serial.print("Pressed Key: ");
  Serial.println(key, DEC);
}

void shift_out(uint32_t bitstream)
{
  // Shift out 24 bits, MSB first
  digitalWrite(SR_nOE, HIGH);
  shiftOut(SR_SER, SR_CLK, MSBFIRST, (bitstream & 0xFF0000) >> 16); // third byte
  shiftOut(SR_SER, SR_CLK, MSBFIRST, (bitstream & 0xFF00) >> 8);    // second byte
  shiftOut(SR_SER, SR_CLK, MSBFIRST, (bitstream & 0xFF));           // first byte
  digitalWrite(SR_nOE, LOW);
}
