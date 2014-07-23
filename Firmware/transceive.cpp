/*
 * Zemote
 * (C) Copyright 2014 Cameron Lai
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the GNU Lesser General Public License
 * (LGPL) version 3.0 which accompanies this distribution, and is available at
 * https://www.gnu.org/licenses/lgpl-3.0.txt
 *
 * Zemote is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 */

#include <IRremote.h>

#include "pins.h"
#include "transceive.h"

// External variables
zemote_decode user_cmd[NUM_SOFT_BUTTONS][NUM_COMMANDS_PER_BUTTON] = {
  0};
char user_cmd_len[9] = {
  0};

// Local variables
int RECV_PIN = IR_RECV_PIN;
IRrecv irrecv(RECV_PIN);
IRsend irsend;
decode_results results;

/**
 * \fn void sndIRStream(unsigned char button)
 * \brief Sends the IR command using the IRremote library
 */
void sndIRStream(unsigned char button)
{
  unsigned long tmpValue;
  int tmpBits;
  if (user_cmd_len[button] > 0)
  {
    int protocol = user_cmd[button][0].decode_type;
    for(int i=0;i<user_cmd_len[button];i++)
    {
      tmpValue = user_cmd[button][i].value;
      tmpBits = user_cmd[button][i].bits;
      switch(protocol){
      case NEC:
        irsend.sendNEC(tmpValue, tmpBits);
        break;
      case SONY:
        irsend.sendSony(tmpValue, tmpBits); 
        break;
      case RC5:
        irsend.sendRC5(tmpValue, tmpBits); 
        break;
      case RC6:
        irsend.sendRC6(tmpValue, tmpBits); 
        break;
      case DISH:
        irsend.sendDISH(tmpValue, tmpBits); 
        break;
      case SHARP:
        irsend.sendSharp(tmpValue, tmpBits); 
        break;
      case PANASONIC:
        irsend.sendPanasonic(tmpValue, tmpBits); 
        break;   
      }
      delay(40);
    }
  }
}

/**
 * \fn void rcvIRStream(unsigned char button)
 * \brief Receives the IR command and saves them to the user_cmd array
 */
void rcvIRStream(unsigned char button)
{
  unsigned char tmpCmd1, tmpCmd2;
  irrecv.enableIRIn(); // Start the receiver
  char user_cmd_index = 0;
  user_cmd_len[button] = 0;

  while(1)
  {
    if (Serial.available() > 1)
    {
      tmpCmd1 = Serial.read();
      tmpCmd2 = Serial.read();
      if (tmpCmd1 == 'F' && tmpCmd2 == '\n') 
      {
        serial_ack('F');
        break;
      }
    }    
    if (irrecv.decode(&results))
    {
      if (results.bits)
      {
        Serial.print("0x");
        Serial.println(results.value, HEX);
        
        // Only extract useful information from decode_results data type
        zemote_decode tmpCmd;
        tmpCmd.decode_type = (unsigned char)results.decode_type;
        tmpCmd.value = (unsigned long)results.value;
        tmpCmd.bits = (unsigned char)results.bits;

        user_cmd[button][user_cmd_index++] = tmpCmd;
        user_cmd_len[button]++;
      }
      irrecv.resume(); // Receive the next value
    }    
    if (user_cmd_len[button] >= NUM_COMMANDS_PER_BUTTON) 
    {
      serial_ack('B');
      break;
    }
  }
}

void serial_ack(char cmd)
{
  Serial.print("ok - ");
  Serial.println(cmd); 
}

void serial_error(char cmd)
{
  Serial.print("error - ");
  Serial.println(cmd);  
}








